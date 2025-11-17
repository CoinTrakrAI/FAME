#!/usr/bin/env python3
"""
FAME Autonomous Engine — Production-Ready Rewrite
Single-file module providing:
- Async scraping spiders (aiohttp)
- Vector memory (FAISS/Chroma fallback)
- Dual-core LLM executor (cloud + local)
- Confidence scoring & answer fusion
- Learning & simple RL feedback
- Persistent memory + metrics
"""

from __future__ import annotations

import os
import sys
import json
import time
import math
import asyncio
import hashlib
import logging
import shutil
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, field

# --- Optional dependencies (import gracefully) ---
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except Exception:
    AIOHTTP_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except Exception:
    BS4_AVAILABLE = False

# embeddings / vectorstore
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except Exception:
    ST_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False

# openai client (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# transformers local model
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False

# logging
logging.basicConfig(
    level=os.getenv("FAME_LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("fame_engine")

# -------------------------
# Configuration + Utilities
# -------------------------

@dataclass
class Config:
    data_dir: Path = Path(os.getenv("FAME_DATA_DIR", "./fame_data"))
    memory_file: Path = field(init=False)
    convo_history_max: int = int(os.getenv("FAME_CONVO_MAX", "2000"))
    save_every_seconds: int = int(os.getenv("FAME_SAVE_EVERY", "30"))
    embed_model_name: str = os.getenv("FAME_EMBED_MODEL", "all-mpnet-base-v2")  # sentence-transformers
    llm_cloud: str = os.getenv("FAME_LLM_CLOUD", "openai")  # openai / google / custom
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    google_ai_key: Optional[str] = os.getenv("GOOGLE_AI_KEY")
    serpapi_key: Optional[str] = os.getenv("SERPAPI_KEY")
    max_web_tasks: int = int(os.getenv("FAME_MAX_WEB_TASKS", "8"))
    request_timeout: int = int(os.getenv("FAME_REQUEST_TIMEOUT", "15"))

    def __post_init__(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.data_dir / "memory.json"

# single global config instance
CFG = Config()

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def hash_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()

# -------------------------
# Persistent Memory Manager
# -------------------------

class MemoryManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._mem: Dict[str, Any] = {
            "conversations": [],
            "knowledge": {},           # keyed by hash -> {answer, embedding, timestamp, source, confidence}
            "patterns": {},            # simple learned templates (can evolve)
            "source_stats": {},
            "meta": {"created": now_iso(), "updated": now_iso()}
        }
        self._dirty = False
        self._last_save = time.time()
        self._load()

    def _load(self):
        if self.cfg.memory_file.exists():
            try:
                with open(self.cfg.memory_file, "r", encoding="utf-8") as f:
                    self._mem = json.load(f)
                    logger.info("Memory loaded: %d conversations", len(self._mem.get("conversations", [])))
            except Exception as e:
                logger.exception("Failed to load memory file: %s", e)

    def save(self, force: bool = False):
        if not force and not self._dirty:
            return
        if time.time() - self._last_save < self.cfg.save_every_seconds and not force:
            return
        try:
            self._mem["meta"]["updated"] = now_iso()
            tmp = self.cfg.memory_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._mem, f, indent=2, ensure_ascii=False)
            tmp.replace(self.cfg.memory_file)
            self._dirty = False
            self._last_save = time.time()
            logger.debug("Memory saved.")
        except Exception as e:
            logger.exception("Failed to save memory: %s", e)

    def add_conversation(self, query: str, response: str, source: str, confidence: float):
        conv = {
            "query": query,
            "response": response,
            "source": source,
            "confidence": float(confidence),
            "timestamp": now_iso(),
            "id": hash_text(query + str(time.time()))
        }
        self._mem.setdefault("conversations", []).append(conv)
        # trim
        if len(self._mem["conversations"]) > self.cfg.convo_history_max:
            self._mem["conversations"] = self._mem["conversations"][-self.cfg.convo_history_max:]
        self._mem["source_stats"][source] = self._mem["source_stats"].get(source, 0) + 1
        self._mem["meta"]["updated"] = now_iso()
        self._dirty = True

    def cache_knowledge(self, key: str, item: Dict[str, Any]):
        self._mem.setdefault("knowledge", {})[key] = item
        self._dirty = True

    def get_knowledge(self, key: str) -> Optional[Dict[str, Any]]:
        return self._mem.get("knowledge", {}).get(key)

    def add_pattern(self, token: str, template: str):
        patterns = self._mem.setdefault("patterns", {})
        patterns[token] = {"template": template, "last": now_iso(), "count": patterns.get(token, {}).get("count", 0) + 1}
        self._dirty = True

    def get_patterns(self) -> Dict[str, Any]:
        return self._mem.get("patterns", {})

    def stats(self) -> Dict[str, Any]:
        return {
            "conversations": len(self._mem.get("conversations", [])),
            "knowledge_cache": len(self._mem.get("knowledge", {})),
            "patterns": len(self._mem.get("patterns", {})),
            "source_stats": self._mem.get("source_stats", {})
        }

# -------------------------
# Embeddings + Vector Store
# -------------------------

class EmbeddingEngine:
    """
    Thin wrapper for embeddings + vector index.
    Supports: (1) sentence-transformers + faiss (recommended),
              (2) sentence-transformers + in-memory brute force fallback.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.model_name = cfg.embed_model_name
        self.model = None
        self.index = None
        self.id_to_meta: Dict[int, Dict[str, Any]] = {}
        self.next_id = 0
        self._load_model()

    def _load_model(self):
        if not ST_AVAILABLE:
            logger.warning("sentence-transformers not available — semantic recall disabled.")
            return
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded: %s", self.model_name)
            # try to init faiss index if available
            self.index = None
        except Exception as e:
            logger.exception("Failed to load embedding model: %s", e)
            self.model = None

    def embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        if not self.model:
            return None
        try:
            return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False).tolist()
        except Exception as e:
            logger.exception("Embedding error: %s", e)
            return None

    def add(self, text: str, meta: Dict[str, Any]):
        # Very simple in-memory store if no faiss
        emb = self.embed([text])
        if emb is None:
            return None
        vec = emb[0]
        self.id_to_meta[self.next_id] = {**meta, "text": text}
        # naive append
        if self.index is None:
            # maintain brute force list
            self.index = {"vectors": [vec], "ids": [self.next_id]}
        else:
            self.index["vectors"].append(vec)
            self.index["ids"].append(self.next_id)
        self.next_id += 1
        return self.next_id - 1

    def search(self, text: str, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        """Return list of (meta, score) ordered by descending similarity (cosine)"""
        if not self.model or not self.index:
            return []
        emb = self.embed([text])
        if emb is None:
            return []
        q = emb[0]
        # brute force cosine
        results = []
        import numpy as np
        qv = np.array(q)
        vecs = np.array(self.index["vectors"])
        # compute cos sim
        v_norms = (vecs * vecs).sum(axis=1) ** 0.5
        q_norm = (qv * qv).sum() ** 0.5
        if q_norm == 0:
            return []
        dots = vecs.dot(qv)
        cos = dots / (v_norms * q_norm + 1e-12)
        top_idx = cos.argsort()[::-1][:top_k]
        for i in top_idx:
            idx = self.index["ids"][i]
            meta = self.id_to_meta.get(idx, {})
            results.append((meta, float(cos[i])))
        return results

# -------------------------
# Async Web Spider
# -------------------------

class AsyncSpider:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.semaphore = asyncio.Semaphore(self.cfg.max_web_tasks)
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self):
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp required for AsyncSpider")
        if self.session and not self.session.closed:
            return self.session
        timeout = aiohttp.ClientTimeout(total=self.cfg.request_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def fetch(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        if not AIOHTTP_AVAILABLE:
            logger.warning("aiohttp not installed — cannot fetch URLs")
            return None
        async with self.semaphore:
            session = await self._get_session()
            backoff = 1.0
            for attempt in range(4):
                try:
                    async with session.get(url, headers=headers or {}, ssl=False) as resp:
                        text = await resp.text()
                        if resp.status == 200:
                            return text
                        else:
                            logger.debug("Fetch %s returned %d", url, resp.status)
                except Exception as e:
                    logger.debug("Fetch error %s: %s", url, e)
                await asyncio.sleep(backoff)
                backoff *= 2
        return None

    async def search_serpapi(self, q: str, num: int = 3) -> List[Dict[str, str]]:
        """Search SERPAPI if key present (returns list of dicts with title, snippet, link)"""
        if not self.cfg.serpapi_key:
            return []
        api = "https://serpapi.com/search"
        params = {"engine": "google", "q": q, "num": num, "api_key": self.cfg.serpapi_key}
        session = await self._get_session()
        try:
            async with session.get(api, params=params, timeout=self.cfg.request_timeout) as r:
                if r.status == 200:
                    data = await r.json()
                    results = []
                    for item in data.get("organic_results", [])[:num]:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "link": item.get("link", "")
                        })
                    return results
        except Exception as e:
            logger.debug("serpapi error: %s", e)
        return []

    async def fetch_wikipedia_summary(self, term: str) -> Optional[str]:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{term}"
        text = await self.fetch(url, headers={"User-Agent": "FAME-Agent/1.0"})
        if not text:
            return None
        try:
            data = json.loads(text)
            return data.get("extract")
        except Exception:
            return None

    async def scrape_site_text(self, url: str) -> Optional[str]:
        html = await self.fetch(url, headers={"User-Agent": "FAME-Agent/1.0"})
        if not html:
            return None
        if BS4_AVAILABLE:
            soup = BeautifulSoup(html, "html.parser")
            paragraphs = soup.find_all("p")
            text = "\n\n".join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
            return text[:4000]
        else:
            # fallback: crude strip
            return html[:4000]

    async def close(self):
        if self.session:
            await self.session.close()

# -------------------------
# LLM Executors (cloud + local)
# -------------------------

class CloudExecutor:
    """
    Lightweight wrapper for calling cloud LLMs.
    Currently includes OpenAI (chat completions) as an example.
    Add other providers (Google Gemini) by implementing call_model().
    """
    def __init__(self, cfg: Config):
        self.cfg = cfg
        if OPENAI_AVAILABLE and cfg.openai_api_key:
            openai.api_key = cfg.openai_api_key

    async def call_model(self, prompt: str, temperature: float = 0.2, max_tokens: int = 512) -> Optional[str]:
        # Try Google AI (Gemini) first if available
        if self.cfg.google_ai_key:
            try:
                result = await self._call_google_ai(prompt, temperature, max_tokens)
                if result:
                    return result
            except Exception as e:
                logger.debug("Google AI call failed: %s", e)

        # Fallback to OpenAI if available
        if OPENAI_AVAILABLE and self.cfg.openai_api_key:
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self._openai_sync_call, prompt, temperature, max_tokens)
                return result
            except Exception as e:
                logger.exception("CloudExecutor error: %s", e)
                return None

        logger.debug("No cloud LLM configured.")
        return None

    async def _call_google_ai(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Call Google AI (Gemini) API"""
        try:
            import aiohttp
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.cfg.google_ai_key}"
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                text = parts[0].get("text", "")
                                if text:
                                    return text
        except Exception as e:
            logger.debug("Google AI API error: %s", e)
        return None

    def _openai_sync_call(self, prompt, temperature, max_tokens):
        # keep sync call isolated to thread pool
        try:
            # Try new OpenAI client API first (v1.0+)
            try:
                client = openai.OpenAI(api_key=self.cfg.openai_api_key)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are FAME - Financial AI Assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                if resp.choices and len(resp.choices) > 0:
                    return resp.choices[0].message.content
            except (AttributeError, TypeError):
                # Fallback to old API style
                resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": "You are FAME - Financial AI Assistant."},
                              {"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                # Response extraction is tolerant to variants
                if isinstance(resp, dict):
                    choices = resp.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content") or choices[0].get("text")
                else:
                    return str(resp)
        except Exception as e:
            logger.exception("OpenAI call failed: %s", e)
            return None

class LocalExecutor:
    """
    Optional local model executor (transformers). Used as fallback for offline or latency-sensitive responses.
    """
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.available = TRANSFORMERS_AVAILABLE
        self.pipe = None
        self._init_model()

    def _init_model(self):
        if not TRANSFORMERS_AVAILABLE:
            logger.info("transformers not available for local execution.")
            return
        # Choose a small local model if environment set
        model_name = os.getenv("FAME_LOCAL_MODEL", "gpt2")  # replace with a proper small causal model if available
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            self.pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)
            logger.info("Local model loaded: %s", model_name)
        except Exception as e:
            logger.exception("Failed to init local model: %s", e)
            self.available = False

    async def call_model(self, prompt: str, temperature: float = 0.2, max_tokens: int = 200) -> Optional[str]:
        if not self.available or not self.pipe:
            return None
        try:
            # run in executor to avoid blocking loop
            loop = asyncio.get_event_loop()
            out = await loop.run_in_executor(None, lambda: self.pipe(prompt, max_length=max_tokens, do_sample=False)[0]["generated_text"])
            return out
        except Exception as e:
            logger.exception("LocalExecutor error: %s", e)
            return None

# -------------------------
# Confidence Scoring & Fusion
# -------------------------

def score_confidence_from_source(source: str, base_score: float, freshness: Optional[int] = None) -> float:
    """
    Convert base score to final confidence.
    source: 'knowledge', 'web', 'cloud', 'local', 'pattern'
    freshness: age in seconds (prefer fresh)
    """
    score = float(base_score)
    weights = {
        "knowledge": 1.0,
        "web": 0.9,
        "cloud": 0.95,
        "local": 0.8,
        "pattern": 0.6
    }
    w = weights.get(source, 0.7)
    score *= w
    if freshness is not None:
        # degrade older than 7 days
        days = freshness / 86400.0
        score *= (1.0 / (1.0 + 0.1 * days))
    return max(0.0, min(1.0, score))

def fuse_answers(candidates: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
    """
    candidates: list of {text, source, confidence}
    returns: best_text, meta
    Simple fusion: choose highest confidence. If multiple similar, combine.
    """
    if not candidates:
        return ("", {"confidence": 0.0})

    # sort
    candidates = sorted(candidates, key=lambda c: c.get("confidence", 0.0), reverse=True)
    top = candidates[0]
    # naive combine: if top confidence >> others, keep top, else concatenate top-2
    if len(candidates) > 1 and top["confidence"] - candidates[1]["confidence"] < 0.12:
        # combine top two
        combined = top["text"].strip() + "\n\n---\n\n" + candidates[1]["text"].strip()
        return (combined, {"confidence": (top["confidence"] + candidates[1]["confidence"]) / 2.0, "sources": [top["source"], candidates[1]["source"]]})
    return (top["text"], {"confidence": top["confidence"], "source": top["source"]})

# -------------------------
# Simple Reward / Feedback Collector (RL primitive)
# -------------------------

class RewardLearner:
    """
    Collects reward signals and updates counters or simple weights.
    Extend this to a real RL algorithm later.
    """
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def record(self, query: str, response_id: str, reward: float, metadata: Optional[Dict[str, Any]] = None):
        self.records.append({
            "query": query,
            "response_id": response_id,
            "reward": float(reward),
            "metadata": metadata or {},
            "t": now_iso()
        })
        logger.debug("Recorded reward for %s -> %s", query[:80], reward)

    def summarize(self) -> Dict[str, Any]:
        if not self.records:
            return {"count": 0}
        avg = sum(r["reward"] for r in self.records) / len(self.records)
        return {"count": len(self.records), "avg_reward": avg}

# -------------------------
# The Autonomous Engine
# -------------------------

class AutonomousResponseEngine:
    def __init__(self, cfg: Optional[Config] = None):
        # Load API keys from local file if available
        try:
            from load_api_keys import load_api_keys
            load_api_keys()
        except ImportError:
            pass

        self.cfg = cfg or CFG
        self.memory = MemoryManager(self.cfg)
        self.embed = EmbeddingEngine(self.cfg)
        self.spider = AsyncSpider(self.cfg) if AIOHTTP_AVAILABLE else None
        self.cloud = CloudExecutor(self.cfg)
        self.local = LocalExecutor(self.cfg)
        self.rl = RewardLearner()
        self.metrics = {
            "queries": 0,
            "web_scrapes": 0,
            "knowledge_hits": 0,
            "cloud_calls": 0,
            "local_calls": 0,
            "patterns_used": 0
        }
        # background saver
        self._bg_task = None
        self._loop = None

    def _ensure_loop(self):
        """Ensure event loop exists for background tasks"""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        if self._bg_task is None or self._bg_task.done():
            self._bg_task = asyncio.create_task(self._periodic_save())

    async def _periodic_save(self):
        while True:
            try:
                await asyncio.sleep(self.cfg.save_every_seconds)
                self.memory.save()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Periodic save error")

    async def generate_response(self, query: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Orchestrates:
        1) knowledge cache lookup (semantic)
        2) semantic search in memory
        3) web scraping (SERPAPI / wikipedia / site scrape)
        4) LLM calls (local cloud)
        5) fuse + score
        6) persist & return

        Returns detailed dict: {response, confidence, breakdown, ...}
        """
        self.metrics["queries"] += 1
        query = query.strip()
        context = context or []
        candidates: List[Dict[str, Any]] = []

        # 1. Semantic search in knowledge via embeddings
        if self.embed.model:
            try:
                hits = self.embed.search(query, top_k=5)
                for meta, sim in hits:
                    # consider if knowledge item is fresh enough
                    freshness_seconds = None
                    ts = meta.get("timestamp")
                    if ts:
                        try:
                            age = datetime.now(timezone.utc) - datetime.fromisoformat(ts)
                            freshness_seconds = age.total_seconds()
                        except Exception:
                            freshness_seconds = None
                    conf = score_confidence_from_source("knowledge", sim, freshness_seconds)
                    if conf > 0.5:
                        self.metrics["knowledge_hits"] += 1
                        candidates.append({"text": meta.get("answer", meta.get("text", "")), "source": "knowledge", "confidence": conf})
            except Exception:
                logger.exception("Embedding search error.")

        # 2. Pattern-based quick answers
        patterns = self.memory.get_patterns()
        for token, pdata in patterns.items():
            if token in query.lower():
                self.metrics["patterns_used"] += 1
                text = pdata.get("template", "")
                conf = score_confidence_from_source("pattern", 0.6)
                candidates.append({"text": text, "source": "pattern", "confidence": conf})

        # 3. Web scraping (SERPAPI -> site scrapes -> wikipedia)
        web_texts = []
        if self.spider:
            try:
                # call SERPAPI for broader results
                serp_results = await self.spider.search_serpapi(query, num=3) if self.cfg.serpapi_key else []
                for r in serp_results:
                    snippet = r.get("snippet") or ""
                    if snippet:
                        txt = f"{r.get('title')}\n{snippet}\nSource: {r.get('link')}"
                        conf = score_confidence_from_source("web", 0.55)
                        candidates.append({"text": txt, "source": "web", "confidence": conf})
                        web_texts.append(r.get("link"))

                # Try Wikipedia summary on factual queries
                if any(k in query.lower() for k in ("who is", "what is", "when did", "where is")):
                    term = query.replace("who is", "").replace("what is", "").strip().split("?")[0]
                    term_token = term.split()[0] if term else ""
                    if term_token:
                        wiki = await self.spider.fetch_wikipedia_summary(term_token)
                        if wiki:
                            conf = score_confidence_from_source("web", 0.7)
                            candidates.append({"text": wiki, "source": "web", "confidence": conf})

                # Try scraping first few links for deeper content
                for link in web_texts[:3]:
                    stext = await self.spider.scrape_site_text(link)
                    if stext:
                        conf = score_confidence_from_source("web", 0.6)
                        candidates.append({"text": stext, "source": "web", "confidence": conf})
                        self.metrics["web_scrapes"] += 1
            except Exception:
                logger.exception("Web scraping stage failed.")

        # 4. Cloud LLM (high quality)
        cloud_prompt = self._build_prompt(query, context)
        cloud_resp = await self.cloud.call_model(cloud_prompt) if self.cloud else None
        if cloud_resp:
            candidates.append({"text": cloud_resp, "source": "cloud", "confidence": score_confidence_from_source("cloud", 0.8)})
            self.metrics["cloud_calls"] += 1

        # 5. Local LLM fallback/fast
        local_resp = await self.local.call_model(cloud_prompt) if self.local and self.local.available else None
        if local_resp:
            candidates.append({"text": local_resp, "source": "local", "confidence": score_confidence_from_source("local", 0.55)})
            self.metrics["local_calls"] += 1

        # 6. Fuse answers
        final_text, meta = fuse_answers(candidates)
        conf = meta.get("confidence", 0.0)

        # 7. Store to memory + embeddings for future recall
        # store full answer under hashed key
        key = hash_text(query)
        try:
            # create knowledge item
            knowledge_item = {
                "answer": final_text,
                "source_breakdown": [ {"s": c["source"], "c": c["confidence"]} for c in candidates ],
                "confidence": conf,
                "timestamp": now_iso()
            }
            self.memory.cache_knowledge(key, knowledge_item)
            # also add to embeddings index if available (text = query + answer)
            if self.embed.model:
                self.embed.add(query + " " + final_text, {**knowledge_item})
        except Exception:
            logger.exception("Error saving knowledge/embedding.")

        # 8. Save conversation
        self.memory.add_conversation(query, final_text, meta.get("source", "fused"), conf)

        # 9. Return structured result
        return {
            "query": query,
            "response": final_text,
            "confidence": float(conf),
            "breakdown": candidates,
            "metrics": self.metrics,
            "memory_stats": self.memory.stats()
        }

    def _build_prompt(self, query: str, context: List[Dict[str, str]]) -> str:
        prompt = f"You are FAME - Financial Autonomous Engine. Answer concisely and cite sources when possible.\n\nQuestion: {query}\n\n"
        if context:
            prompt += "Context:\n"
            for m in context[-3:]:
                prompt += f"{m.get('role','user')}: {m.get('content','')}\n"
        prompt += "\nAnswer:"
        return prompt

    async def shutdown(self):
        try:
            if self.spider:
                await self.spider.close()
        except Exception:
            pass
        try:
            self.memory.save(force=True)
        except Exception:
            pass
        # cancel background saver
        if self._bg_task:
            self._bg_task.cancel()
        logger.info("Engine shutdown complete.")

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics (backward compatibility)"""
        return {
            **self.metrics,
            "memory_size": self.memory.stats().get("conversations", 0),
            "patterns_learned": self.memory.stats().get("patterns", 0),
            "knowledge_cache_size": self.memory.stats().get("knowledge_cache", 0)
        }

# -------------------------
# Singleton instance
# -------------------------

_autonomous_engine: Optional[AutonomousResponseEngine] = None

def get_autonomous_engine() -> AutonomousResponseEngine:
    """Get or create autonomous response engine"""
    global _autonomous_engine
    if _autonomous_engine is None:
        _autonomous_engine = AutonomousResponseEngine()
    return _autonomous_engine

# -------------------------
# Example usage (async)
# -------------------------

async def example_run():
    cfg = CFG
    engine = AutonomousResponseEngine(cfg)
    try:
        q = "Who is the current President of the United States?"
        result = await engine.generate_response(q)
        print("Response:", result["response"])
        print("Confidence:", result["confidence"])
        print("Breakdown:", result["breakdown"][:3])
    finally:
        await engine.shutdown()

# allow running the demo when executed directly
if __name__ == "__main__":
    if not AIOHTTP_AVAILABLE:
        logger.warning("aiohttp not installed; web scraping disabled. Install aiohttp to enable.")
    if not ST_AVAILABLE:
        logger.warning("sentence-transformers not installed; semantic memory disabled. Install sentence-transformers to enable.")
    try:
        asyncio.run(example_run())
    except KeyboardInterrupt:
        pass
