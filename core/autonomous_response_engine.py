#!/usr/bin/env python3
"""
FAME Autonomous Response Engine
Fully dynamic, self-learning system that uses web scraping, stored knowledge, and real-time learning
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

# Try imports
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False


class AutonomousResponseEngine:
    """
    Fully autonomous response engine that:
    1. Uses web scraping for real-time information
    2. Queries stored knowledge base
    3. Uses Google AI for intelligent responses
    4. Learns from every interaction
    5. Evolves continuously
    """
    
    def __init__(self):
        # API Keys (from user)
        self.google_ai_key = os.getenv("GOOGLE_AI_KEY", "AIzaSyA1mrDPxjMV8CJmoYgFPqk4ya23j3gM8OA")
        self.serpapi_key = os.getenv("SERPAPI_KEY", "90f8748cb8ab624df5d503e1765e929491c57ef0b4d681fbe046f1febe045dbc")
        self.serpapi_backup = os.getenv("SERPAPI_BACKUP_KEY", "912dc3fe069c587aa89dc662a492998ded20a25dfc49f9961ff5e5c99168eeb1")
        
        # Knowledge base paths
        self.knowledge_dir = Path("./knowledge_base")
        self.knowledge_dir.mkdir(exist_ok=True)
        self.memory_file = self.knowledge_dir / "fame_autonomous_memory.json"
        
        # Load existing memory
        self.memory = self._load_memory()
        
        # Learning statistics
        self.learning_stats = {
            "total_queries": 0,
            "web_scrapes": 0,
            "knowledge_hits": 0,
            "google_ai_calls": 0,
            "learned_patterns": 0
        }
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load persistent memory"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading memory: {e}")
        
        return {
            "conversations": [],
            "learned_patterns": {},
            "knowledge_cache": {},
            "source_preferences": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_memory(self):
        """Save memory to disk"""
        try:
            self.memory["last_updated"] = datetime.now().isoformat()
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
    
    async def generate_response(self, query: str, context: List[Dict] = None) -> str:
        """
        Generate fully autonomous response using:
        1. Real-time learner recommendations
        2. Stored knowledge
        3. Web scraping
        4. Google AI
        5. Real-time learning
        """
        self.learning_stats["total_queries"] += 1
        
        # Step 0: Check real-time learner for best source
        try:
            from core.real_time_learner import get_real_time_learner
            learner = get_real_time_learner()
            best_source = learner.get_best_source(query)
            learned_template = learner.get_learned_response_template(query)
        except Exception:
            best_source = None
            learned_template = None
        
        # Step 1: Check stored knowledge
        knowledge_result = self._query_knowledge_base(query)
        if knowledge_result and knowledge_result.get("confidence", 0) > 0.7:
            self.learning_stats["knowledge_hits"] += 1
            response = knowledge_result["answer"]
            self._learn_from_interaction(query, response, "knowledge_base")
            return response
        
        # Step 2: Use learned template if available
        if learned_template:
            response = learned_template
            self._learn_from_interaction(query, response, "learned_template")
            return response
        
        # Step 3: Web scraping for real-time information (prioritize if learner recommends)
        if best_source == "web_scraping" or not best_source:
            web_result = await self._scrape_web_info(query)
            if web_result:
                self.learning_stats["web_scrapes"] += 1
                response = web_result
                self._learn_from_interaction(query, response, "web_scraping")
                return response
        
        # Step 4: Use Google AI for intelligent response (prioritize if learner recommends)
        if best_source == "google_ai" or not best_source:
            ai_result = await self._call_google_ai(query, context or [])
            if ai_result:
                self.learning_stats["google_ai_calls"] += 1
                response = ai_result
                self._learn_from_interaction(query, response, "google_ai")
                return response
        
        # Step 5: Fallback - use learned patterns
        pattern_result = self._use_learned_patterns(query)
        if pattern_result:
            response = pattern_result
            self._learn_from_interaction(query, response, "learned_pattern")
            return response
        
        # Final fallback
        return "I'm processing your query. Let me gather more information to provide you with an accurate answer."
    
    def _query_knowledge_base(self, query: str) -> Optional[Dict[str, Any]]:
        """Query stored knowledge base for similar past queries"""
        query_lower = query.lower()
        query_hash = hashlib.md5(query_lower.encode()).hexdigest()
        
        # Check cache
        if query_hash in self.memory.get("knowledge_cache", {}):
            cached = self.memory["knowledge_cache"][query_hash]
            if cached.get("confidence", 0) > 0.7:
                return cached
        
        # Search conversations
        best_match = None
        best_score = 0.0
        
        for conv in self.memory.get("conversations", []):
            past_query = conv.get("query", "").lower()
            if not past_query:
                continue
            
            # Simple similarity (can be enhanced with embeddings)
            similarity = self._calculate_similarity(query_lower, past_query)
            if similarity > best_score and similarity > 0.6:
                best_score = similarity
                best_match = {
                    "answer": conv.get("response", ""),
                    "confidence": similarity,
                    "source": "knowledge_base",
                    "timestamp": conv.get("timestamp")
                }
        
        if best_match:
            # Cache it
            self.memory.setdefault("knowledge_cache", {})[query_hash] = best_match
            return best_match
        
        return None
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate simple word-based similarity"""
        words1 = set(query1.split())
        words2 = set(query2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    async def _scrape_web_info(self, query: str) -> Optional[str]:
        """Dynamically scrape web for real-time information"""
        if not REQUESTS_AVAILABLE:
            return None
        
        try:
            # Try SERPAPI first
            serp_result = await self._search_serpapi(query)
            if serp_result:
                return serp_result
            
            # Try direct web scraping
            web_result = await self._direct_web_scrape(query)
            if web_result:
                return web_result
            
        except Exception as e:
            logger.debug(f"Web scraping error: {e}")
        
        return None
    
    async def _search_serpapi(self, query: str) -> Optional[str]:
        """Search using SERPAPI"""
        api_key = self.serpapi_key or self.serpapi_backup
        if not api_key:
            return None
        
        try:
            url = "https://serpapi.com/search"
            params = {
                "api_key": api_key,
                "q": query,
                "engine": "google",
                "num": 3
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Extract organic results
                for item in data.get("organic_results", [])[:3]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")
                    
                    if snippet:
                        results.append(f"{title}\n{snippet}\nSource: {link}")
                
                if results:
                    return "\n\n".join(results)
        
        except Exception as e:
            logger.debug(f"SERPAPI error: {e}")
        
        return None
    
    async def _direct_web_scrape(self, query: str) -> Optional[str]:
        """Direct web scraping for specific queries"""
        query_lower = query.lower()
        
        # Special handling for common queries
        if "president" in query_lower and "united states" in query_lower:
            return await self._scrape_whitehouse()
        
        # Try Wikipedia for factual queries
        if any(word in query_lower for word in ["who is", "what is", "when did"]):
            wiki_result = await self._scrape_wikipedia(query)
            if wiki_result:
                return wiki_result
        
        return None
    
    async def _scrape_whitehouse(self) -> Optional[str]:
        """Scrape WhiteHouse.gov for current president info"""
        try:
            url = "https://www.whitehouse.gov/"
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200 and BEAUTIFULSOUP_AVAILABLE:
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                
                # Extract president name
                import re
                pres_matches = re.findall(r'President\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|$)', text)
                vp_matches = re.findall(r'Vice\s+President\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|$)', text)
                
                if pres_matches:
                    from collections import Counter
                    president = Counter(pres_matches).most_common(1)[0][0].strip()
                    vp = Counter(vp_matches).most_common(1)[0][0].strip() if vp_matches else "Unknown"
                    
                    return f"The current President of the United States is {president}. The Vice President is {vp}. (Source: whitehouse.gov)"
        
        except Exception as e:
            logger.debug(f"WhiteHouse scrape error: {e}")
        
        return None
    
    async def _scrape_wikipedia(self, query: str) -> Optional[str]:
        """Scrape Wikipedia for factual information"""
        try:
            # Extract search term
            search_term = query.replace("who is", "").replace("what is", "").replace("when did", "").strip()
            search_term = search_term.split()[0] if search_term.split() else ""
            
            if not search_term:
                return None
            
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_term}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                extract = data.get("extract", "")
                if extract:
                    return f"{extract[:500]}... (Source: Wikipedia)"
        
        except Exception as e:
            logger.debug(f"Wikipedia scrape error: {e}")
        
        return None
    
    async def _call_google_ai(self, query: str, context: List[Dict]) -> Optional[str]:
        """Call Google AI (Gemini) for intelligent responses"""
        if not self.google_ai_key:
            return None
        
        try:
            # Use Google Generative AI
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.google_ai_key}"
            
            # Prepare context
            prompt = f"""You are FAME - Financial AI Mastermind Executive. Answer the following question using your knowledge and reasoning.

Question: {query}

Provide a clear, accurate, and helpful response. If you need real-time information, indicate that the user should check current sources."""
            
            if context:
                prompt += "\n\nRecent conversation context:\n"
                for msg in context[-3:]:  # Last 3 messages
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    prompt += f"{role}: {content}\n"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        text = parts[0].get("text", "")
                        if text:
                            return text
        
        except Exception as e:
            logger.debug(f"Google AI error: {e}")
        
        return None
    
    def _use_learned_patterns(self, query: str) -> Optional[str]:
        """Use learned patterns from past interactions"""
        query_lower = query.lower()
        
        patterns = self.memory.get("learned_patterns", {})
        
        # Check for similar patterns
        for pattern_key, pattern_data in patterns.items():
            if pattern_key in query_lower:
                response_template = pattern_data.get("response_template", "")
                if response_template:
                    return response_template
        
        return None
    
    def _learn_from_interaction(self, query: str, response: str, source: str):
        """Learn from every interaction - store patterns and improve"""
        # Store conversation
        conversation = {
            "query": query,
            "response": response,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory.setdefault("conversations", []).append(conversation)
        
        # Keep last 1000 conversations
        if len(self.memory["conversations"]) > 1000:
            self.memory["conversations"] = self.memory["conversations"][-1000:]
        
        # Use real-time learner for advanced learning
        try:
            from core.real_time_learner import get_real_time_learner
            learner = get_real_time_learner()
            learner.learn_from_interaction(query, response, source)
        except Exception as e:
            logger.debug(f"Real-time learner error: {e}")
        
        # Extract patterns
        query_lower = query.lower()
        key_words = [w for w in query_lower.split() if len(w) > 3]
        
        for word in key_words:
            if word not in ["what", "who", "when", "where", "why", "how", "the", "is", "are", "was", "were"]:
                if word not in self.memory.setdefault("learned_patterns", {}):
                    self.memory["learned_patterns"][word] = {
                        "response_template": response[:200],  # First 200 chars
                        "usage_count": 1,
                        "last_used": datetime.now().isoformat(),
                        "source": source
                    }
                    self.learning_stats["learned_patterns"] += 1
                else:
                    pattern = self.memory["learned_patterns"][word]
                    pattern["usage_count"] += 1
                    pattern["last_used"] = datetime.now().isoformat()
        
        # Update source preferences
        source_prefs = self.memory.setdefault("source_preferences", {})
        source_prefs[source] = source_prefs.get(source, 0) + 1
        
        # Save memory periodically
        if self.learning_stats["total_queries"] % 10 == 0:
            self._save_memory()
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            **self.learning_stats,
            "memory_size": len(self.memory.get("conversations", [])),
            "patterns_learned": len(self.memory.get("learned_patterns", {})),
            "knowledge_cache_size": len(self.memory.get("knowledge_cache", {}))
        }


# Global instance
_autonomous_engine = None

def get_autonomous_engine() -> AutonomousResponseEngine:
    """Get or create autonomous response engine"""
    global _autonomous_engine
    if _autonomous_engine is None:
        _autonomous_engine = AutonomousResponseEngine()
    return _autonomous_engine

