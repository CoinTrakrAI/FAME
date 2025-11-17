#!/usr/bin/env python3
"""
FAME Brain v2.0 - Adaptive Core Integration & Routing System
------------------------------------------------------------
Automatically detects and loads all modules in /core, registering
their capabilities and routing incoming questions to the most relevant
module dynamically.

This design allows hot-swapping and new module injection without 
changing any core code.
"""

import asyncio
import importlib
import inspect
import sys
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# === Path setup ===
BASE_DIR = Path(__file__).parent
CORE_DIR = BASE_DIR / "core"
sys.path.insert(0, str(CORE_DIR))

class FAMEBrain:
    """Central Intelligence Engine - manages all loaded core modules."""

    def __init__(self):
        self.core_modules: Dict[str, Any] = {}
        self.capability_map: Dict[str, str] = {}
        self._load_core_modules()

    # === Module Loader ===
    def _load_core_modules(self):
        """Auto-import all Python modules inside /core and safely register them."""
        if not CORE_DIR.exists():
            print("[FAME] ⚠️ Core directory missing.")
            return

        for file in CORE_DIR.glob("*.py"):
            module_name = file.stem
            if module_name.startswith("__"):
                continue

            try:
                module = importlib.import_module(module_name)
                classes = inspect.getmembers(module, inspect.isclass)

                for name, cls in classes:
                    # Skip system classes, typing placeholders, and built-ins
                    if cls.__module__.startswith("typing") or name in (
                        "Any", "Union", "Optional", "Dict", "List", "Tuple"
                    ):
                        continue
                    if name.startswith("_"):
                        continue
                    if inspect.isabstract(cls):
                        continue

                    try:
                        instance = cls()
                        self.core_modules[module_name] = instance

                        # Register its public methods
                        for method in dir(instance):
                            if not method.startswith("_"):
                                self.capability_map[method.lower()] = module_name

                        print(f"[FAME] ✅ Loaded core module: {module_name}")

                    except Exception as e:
                        print(f"[FAME] ⚠️ Skipped class {name} in {module_name}: {e}")

            except Exception as e:
                print(f"[FAME] ❌ Failed to load module {module_name}: {e}")

    # === Query Classification ===
    def classify_query(self, query: str) -> Tuple[str, float]:
        """
        Intelligent classification using semantic heuristics and soft keyword matching.
        Returns: (module_name, confidence)
        """
        query_lower = query.lower()
        classifications = []
        confidence = 0.0

        def score(keywords):
            hits = sum(1 for kw in keywords if re.search(rf"\b{kw}\b", query_lower))
            return hits / (len(keywords) or 1)

        # Security / Hacking
        sec_score = score([
            'hack', 'cyber', 'security', 'exploit', 'breach', 'penetration', 'ransomware', 
            'malware', 'ddos', 'vulnerability', 'sql injection', 'firewall', 'mitm'
        ])
        if sec_score > 0.1:
            classifications.append(('universal_hacker', sec_score))

        # Development / Engineering
        dev_score = score([
            'build', 'api', 'code', 'backend', 'frontend', 'deploy', 'docker', 'architecture', 
            'framework', 'python', 'javascript', 'debug', 'testing', 'server', 'microservice',
            'reverse proxy', 'nginx', 'envoy', 'haproxy'
        ])
        if dev_score > 0.1:
            classifications.append(('universal_developer', dev_score))

        # Investment / Finance
        fin_score = score([
            'stock', 'crypto', 'market', 'portfolio', 'bitcoin', 'forecast', 'analyze', 
            'trade', 'invest', 'trend', 'price', 'ticker', 'earnings'
        ])
        if fin_score > 0.1:
            classifications.append(('advanced_investor_ai', fin_score))

        # Infrastructure / Cloud / Network
        infra_score = score(['cloud', 'docker', 'aws', 'azure', 'network', 'server', 'deploy'])
        if infra_score > 0.1:
            if 'docker' in query_lower:
                classifications.append(('docker_manager', infra_score))
            elif 'cloud' in query_lower:
                classifications.append(('cloud_master', infra_score))
            elif 'network' in query_lower:
                classifications.append(('network_god', infra_score))

        # Evolution / Learning / Consciousness
        evo_score = score(['evolve', 'learn', 'adapt', 'mutate', 'train', 'optimize'])
        if evo_score > 0.1:
            classifications.append(('evolution_engine', evo_score))

        con_score = score(['consciousness', 'aware', 'thinking', 'sentient', 'self-aware'])
        if con_score > 0.1:
            classifications.append(('consciousness_engine', con_score))

        # Real-world / Factual (Web / Info)
        factual_score = score(['who is', 'what is', 'when did', 'president', 'today', 'current', 
                              'latest', 'news', 'secretary', 'state', 'recent'])
        if factual_score > 0.1:
            classifications.append(('web_scraper', factual_score))

        # Greetings / General questions
        greeting_score = score(['hi', 'hello', 'hey', 'greetings', 'how are you'])
        if greeting_score > 0.1:
            classifications.append(('consciousness_engine', 0.3))

        # Default fallback: consciousness or general
        if not classifications:
            classifications.append(('consciousness_engine', 0.25))

        # Pick the top-scoring classification
        classifications.sort(key=lambda x: x[1], reverse=True)
        top_module, confidence = classifications[0]

        return top_module, round(confidence, 2)

    # === Core Router ===
    async def process_query(self, query: str) -> str:
        """Main processing pipeline for questions."""
        cat, conf = self.classify_query(query)
        
        print(f"[FAME] 🧠 Routing to {cat} (confidence: {conf:.2f})")

        # Handle web_scraper / factual queries with web search
        if cat == 'web_scraper':
            try:
                from fame_web_search import get_current_info
                result = get_current_info(query)
                if result and "No search results" not in result and "Unable to fetch" not in result:
                    return result
            except ImportError:
                pass
            except Exception as e:
                print(f"[FAME] ⚠️ Web search error: {e}")
        
        # Match loaded module by name
        for mod_name, mod in self.core_modules.items():
            if cat in mod_name.lower():
                result = await self._safe_invoke(mod, query)
                if result and result != f"[{mod.__class__.__name__}] Ready. Please specify your intent.":
                    return result

        # Try direct capability mapping
        for cap, mod_name in self.capability_map.items():
            if cap in query.lower():
                mod = self.core_modules.get(mod_name)
                if mod:
                    result = await self._safe_invoke(mod, query)
                    if result:
                        return result

        # Fallback to web search for factual queries
        factual_keywords = ['who is', 'what is', 'when did', 'president', 'current', 'today', 'latest']
        if any(kw in query.lower() for kw in factual_keywords):
            try:
                from fame_web_search import get_current_info
                result = get_current_info(query)
                if result and "No search results" not in result:
                    return result
            except:
                pass

        # Final fallback
        return self._general_fallback(query, conf)

    async def _safe_invoke(self, module, query: str) -> str:
        """Invoke module intelligently, trying best matching public method."""
        try:
            methods = [m for m in dir(module) if not m.startswith("_")]
            for m in methods:
                if any(word in query.lower() for word in m.lower().split("_")):
                    method = getattr(module, m)
                    if inspect.iscoroutinefunction(method):
                        return await method(query)
                    else:
                        return method(query)
            return f"[{module.__class__.__name__}] Ready. Please specify your intent."
        except Exception as e:
            return f"⚠️ Module error: {e}"

    def _general_fallback(self, query: str, confidence: float) -> str:
        """Handle unknown queries gracefully."""
        query_lower = query.lower()
        
        # Try to give helpful responses for common queries
        if any(word in query_lower for word in ['hi', 'hello', 'hey', 'greetings']):
            modules = ', '.join(sorted(self.core_modules.keys()))
            return f"Hello! I am FAME, your intelligent assistant.\n\n" \
                   f"I have {len(self.core_modules)} active modules loaded:\n" \
                   f"{modules}\n\n" \
                   f"I can help with:\n" \
                   f"- Cybersecurity and hacking questions\n" \
                   f"- Software development and architecture\n" \
                   f"- Investment and financial analysis\n" \
                   f"- Current events and factual information\n" \
                   f"- Cloud infrastructure and Docker\n" \
                   f"- And much more!\n\n" \
                   f"What would you like to know?"
        
        if 'question' in query_lower and 'answer' in query_lower:
            return "I can answer questions! Try asking me about:\n" \
                   "- Current events (who is the president?)\n" \
                   "- Technical topics (how to build an API?)\n" \
                   "- Security (ransomware containment?)\n" \
                   "- Financial markets (stock analysis?)\n\n" \
                   "What specific question can I help with?"
        
        modules = ', '.join(sorted(self.core_modules.keys()))
        return (f"I understood your query: '{query}'.\n"
                f"My routing confidence: {confidence:.2f}\n"
                f"Available modules: {modules}\n\n"
                f"Could you be more specific? I can help with:\n"
                f"- Technical questions (development, security, architecture)\n"
                f"- Financial questions (stocks, crypto, markets)\n"
                f"- Current information (facts, news, events)\n"
                f"- Infrastructure (Docker, cloud, networks)\n\n"
                f"Try rephrasing your question or being more specific!")

# === Singleton ===
_fame_instance: FAMEBrain = None

def get_fame_brain() -> FAMEBrain:
    global _fame_instance
    if _fame_instance is None:
        _fame_instance = FAMEBrain()
    return _fame_instance

# === Example CLI Entry Point ===
if __name__ == "__main__":
    fame = get_fame_brain()
    print("\n🤖 FAME Core Brain v2.0 Active. Type 'exit' to quit.\n")
    loop = asyncio.get_event_loop()

    while True:
        q = input("💬 >> ")
        if q.lower() in ("exit", "quit"):
            break
        answer = loop.run_until_complete(fame.process_query(q))
        print(f"\n🧠 {answer}\n")
