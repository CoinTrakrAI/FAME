#!/usr/bin/env python3
"""
FAME AGI - Autonomous Learning & Pattern Evolution
Template learning, behavioral cloning, query clustering, and pattern distillation
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class AutonomousLearner:
    """
    Autonomous learning system that evolves patterns, summarizes, merges, and generalizes.
    FAME evolves logic, not just stores it.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data_dir = Path(config.get("memory", {}).get("data_dir", "./fame_data"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Pattern storage
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.query_clusters: Dict[str, List[str]] = defaultdict(list)
        self.behavioral_templates: Dict[str, Any] = {}
        
        # Learning statistics
        self.learning_stats = {
            "patterns_learned": 0,
            "patterns_merged": 0,
            "patterns_generalized": 0,
            "queries_clustered": 0,
            "summaries_created": 0
        }
        
        self._load_patterns()
    
    def learn_from_interaction(self, query: str, response: str, reward: float, 
                              context: Optional[Dict[str, Any]] = None):
        """Learn from interaction and evolve patterns"""
        context = context or {}
        
        # Extract pattern
        pattern = self._extract_pattern(query, response)
        
        # Cluster query
        cluster_id = self._cluster_query(query)
        self.query_clusters[cluster_id].append(query)
        self.learning_stats["queries_clustered"] += 1
        
        # Update or create pattern
        pattern_id = self._get_pattern_id(pattern)
        if pattern_id in self.patterns:
            self._merge_pattern(pattern_id, pattern, reward)
            self.learning_stats["patterns_merged"] += 1
        else:
            self.patterns[pattern_id] = {
                "pattern": pattern,
                "response_template": response,
                "usage_count": 1,
                "avg_reward": reward,
                "last_used": time.time(),
                "created_at": time.time()
            }
            self.learning_stats["patterns_learned"] += 1
        
        # Behavioral cloning (if high reward)
        if reward > 0.7:
            self._clone_behavior(query, response, context)
        
        # Periodic summarization
        if len(self.patterns) % 10 == 0:
            self._summarize_patterns()
    
    def _extract_pattern(self, query: str, response: str) -> Dict[str, Any]:
        """Extract pattern from query-response pair"""
        # Extract key components
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        # Find common important words
        important_words = [w for w in query_words if len(w) > 3 and w not in ["what", "how", "when", "where"]]
        
        # Extract intent keywords
        intent_keywords = []
        if any(w in query.lower() for w in ["price", "cost", "value"]):
            intent_keywords.append("price_query")
        if any(w in query.lower() for w in ["analyze", "analysis", "trend"]):
            intent_keywords.append("analysis_query")
        if any(w in query.lower() for w in ["create", "build", "make"]):
            intent_keywords.append("creation_query")
        
        return {
            "keywords": important_words[:5],
            "intent": intent_keywords,
            "query_length": len(query.split()),
            "response_length": len(response.split()),
            "query_structure": self._analyze_structure(query)
        }
    
    def _analyze_structure(self, query: str) -> str:
        """Analyze query structure"""
        if "?" in query:
            if query.startswith(("what", "who", "when", "where", "why", "how")):
                return "question_wh"
            return "question_yesno"
        elif any(word in query.lower() for word in ["analyze", "compare", "evaluate"]):
            return "command_analysis"
        elif any(word in query.lower() for word in ["create", "build", "make"]):
            return "command_creation"
        return "statement"
    
    def _cluster_query(self, query: str) -> str:
        """Cluster query into similar groups"""
        # Simple clustering based on keywords
        query_lower = query.lower()
        key_words = [w for w in query_lower.split() if len(w) > 4]
        
        if not key_words:
            return "general"
        
        # Use first significant word as cluster
        cluster_word = key_words[0]
        return f"cluster_{cluster_word}"
    
    def _get_pattern_id(self, pattern: Dict[str, Any]) -> str:
        """Generate pattern ID"""
        pattern_str = json.dumps(pattern, sort_keys=True)
        return hashlib.sha256(pattern_str.encode()).hexdigest()[:16]
    
    def _merge_pattern(self, pattern_id: str, new_pattern: Dict[str, Any], reward: float):
        """Merge new pattern into existing"""
        existing = self.patterns[pattern_id]
        
        # Update usage
        existing["usage_count"] += 1
        
        # Update reward (exponential moving average)
        alpha = 0.1
        existing["avg_reward"] = alpha * reward + (1 - alpha) * existing["avg_reward"]
        
        # Merge keywords
        existing_keywords = set(existing["pattern"].get("keywords", []))
        new_keywords = set(new_pattern.get("keywords", []))
        merged_keywords = list(existing_keywords.union(new_keywords))[:10]
        existing["pattern"]["keywords"] = merged_keywords
        
        existing["last_used"] = time.time()
    
    def _clone_behavior(self, query: str, response: str, context: Dict[str, Any]):
        """Behavioral cloning for high-reward interactions"""
        template_id = f"template_{hashlib.sha256(query.encode()).hexdigest()[:12]}"
        
        self.behavioral_templates[template_id] = {
            "query_template": query,
            "response_template": response,
            "context": context,
            "reward": context.get("reward", 1.0),
            "created_at": time.time()
        }
    
    def _summarize_patterns(self):
        """Summarize and generalize patterns"""
        # Find similar patterns
        pattern_groups = self._group_similar_patterns()
        
        for group_id, pattern_ids in pattern_groups.items():
            if len(pattern_ids) > 1:
                # Merge similar patterns
                merged = self._generalize_patterns(pattern_ids)
                # Remove individual patterns, keep merged
                for pid in pattern_ids[1:]:
                    if pid in self.patterns:
                        del self.patterns[pid]
                
                self.learning_stats["patterns_generalized"] += 1
                self.learning_stats["summaries_created"] += 1
    
    def _group_similar_patterns(self) -> Dict[str, List[str]]:
        """Group similar patterns together"""
        groups = defaultdict(list)
        
        for pattern_id, pattern_data in self.patterns.items():
            keywords = pattern_data["pattern"].get("keywords", [])
            if keywords:
                # Use first keyword as group identifier
                group_key = keywords[0]
                groups[group_key].append(pattern_id)
        
        # Filter groups with multiple patterns
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def _generalize_patterns(self, pattern_ids: List[str]) -> Dict[str, Any]:
        """Generalize multiple patterns into one"""
        patterns = [self.patterns[pid] for pid in pattern_ids if pid in self.patterns]
        if not patterns:
            return {}
        
        # Merge all patterns
        all_keywords = set()
        all_intents = set()
        total_reward = 0.0
        total_count = 0
        
        for p in patterns:
            all_keywords.update(p["pattern"].get("keywords", []))
            all_intents.update(p["pattern"].get("intent", []))
            total_reward += p["avg_reward"] * p["usage_count"]
            total_count += p["usage_count"]
        
        generalized = {
            "pattern": {
                "keywords": list(all_keywords)[:10],
                "intent": list(all_intents),
                "query_length": "variable",
                "response_length": "variable",
                "query_structure": "variable"
            },
            "response_template": patterns[0]["response_template"],  # Use first as template
            "usage_count": total_count,
            "avg_reward": total_reward / total_count if total_count > 0 else 0.0,
            "last_used": time.time(),
            "created_at": time.time(),
            "generalized_from": pattern_ids
        }
        
        # Store generalized pattern
        pattern_id = self._get_pattern_id(generalized["pattern"])
        self.patterns[pattern_id] = generalized
        
        return generalized
    
    def get_pattern(self, query: str) -> Optional[Dict[str, Any]]:
        """Get matching pattern for query"""
        query_pattern = self._extract_pattern(query, "")
        
        # Find best matching pattern
        best_match = None
        best_score = 0.0
        
        for pattern_id, pattern_data in self.patterns.items():
            pattern = pattern_data["pattern"]
            score = self._pattern_similarity(query_pattern, pattern)
            
            if score > best_score and score > 0.6:
                best_score = score
                best_match = pattern_data
        
        return best_match
    
    def _pattern_similarity(self, pattern1: Dict[str, Any], pattern2: Dict[str, Any]) -> float:
        """Calculate similarity between patterns"""
        keywords1 = set(pattern1.get("keywords", []))
        keywords2 = set(pattern2.get("keywords", []))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def _load_patterns(self):
        """Load patterns from disk"""
        patterns_file = self.data_dir / "learned_patterns.json"
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    self.patterns = data.get("patterns", {})
                    self.query_clusters = defaultdict(list, data.get("clusters", {}))
                    self.learning_stats = data.get("stats", self.learning_stats)
                logger.info(f"Loaded {len(self.patterns)} patterns")
            except Exception as e:
                logger.error(f"Failed to load patterns: {e}")
    
    def save_patterns(self):
        """Save patterns to disk"""
        patterns_file = self.data_dir / "learned_patterns.json"
        try:
            data = {
                "patterns": self.patterns,
                "clusters": dict(self.query_clusters),
                "stats": self.learning_stats
            }
            with open(patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Patterns saved")
        except Exception as e:
            logger.error(f"Failed to save patterns: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            **self.learning_stats,
            "total_patterns": len(self.patterns),
            "total_clusters": len(self.query_clusters),
            "behavioral_templates": len(self.behavioral_templates)
        }

