#!/usr/bin/env python3
"""
FAME Real-Time Learning System
Continuously learns and evolves from every interaction
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class RealTimeLearner:
    """
    Real-time learning system that:
    1. Learns from every query-response pair
    2. Identifies successful patterns
    3. Adapts response strategies
    4. Evolves continuously
    """
    
    def __init__(self, learning_dir: str = "./learning_data"):
        self.learning_dir = Path(learning_dir)
        self.learning_dir.mkdir(exist_ok=True)
        
        self.patterns_file = self.learning_dir / "learned_patterns.json"
        self.success_file = self.learning_dir / "success_metrics.json"
        
        # Load existing patterns
        self.patterns = self._load_patterns()
        self.success_metrics = self._load_success_metrics()
        
        # Real-time learning stats
        self.stats = {
            "total_learnings": 0,
            "patterns_extracted": 0,
            "strategies_improved": 0,
            "last_learning": None
        }
    
    def _load_patterns(self) -> Dict[str, Any]:
        """Load learned patterns"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading patterns: {e}")
        
        return {
            "query_patterns": {},
            "response_templates": {},
            "source_effectiveness": {},
            "topic_clusters": {}
        }
    
    def _load_success_metrics(self) -> Dict[str, Any]:
        """Load success metrics"""
        if self.success_file.exists():
            try:
                with open(self.success_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading success metrics: {e}")
        
        return {
            "source_success_rates": {},
            "response_quality_scores": {},
            "user_satisfaction": {},
            "improvement_trends": []
        }
    
    def learn_from_interaction(self, query: str, response: str, source: str, 
                              user_feedback: Optional[float] = None):
        """
        Learn from a single interaction
        - Extract patterns
        - Update success metrics
        - Improve strategies
        """
        self.stats["total_learnings"] += 1
        self.stats["last_learning"] = datetime.now().isoformat()
        
        # Extract query patterns
        query_pattern = self._extract_query_pattern(query)
        if query_pattern:
            self._update_pattern(query_pattern, response, source)
            self.stats["patterns_extracted"] += 1
        
        # Update source effectiveness
        self._update_source_effectiveness(source, response, user_feedback)
        
        # Extract response quality
        quality_score = self._assess_response_quality(response, query)
        self._update_quality_metrics(query, response, quality_score, source)
        
        # Save periodically
        if self.stats["total_learnings"] % 20 == 0:
            self._save_learning_data()
    
    def _extract_query_pattern(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract pattern from query"""
        query_lower = query.lower()
        
        # Identify question type
        question_type = None
        if query_lower.startswith("what"):
            question_type = "factual"
        elif query_lower.startswith("who"):
            question_type = "person"
        elif query_lower.startswith("when"):
            question_type = "temporal"
        elif query_lower.startswith("where"):
            question_type = "location"
        elif query_lower.startswith("why"):
            question_type = "explanatory"
        elif query_lower.startswith("how"):
            question_type = "procedural"
        
        # Extract key entities
        entities = []
        key_words = [w for w in query_lower.split() if len(w) > 3]
        entities = [w for w in key_words if w not in ["what", "who", "when", "where", "why", "how", "the", "is", "are"]]
        
        if question_type or entities:
            return {
                "question_type": question_type,
                "entities": entities,
                "query_length": len(query),
                "has_numbers": any(char.isdigit() for char in query)
            }
        
        return None
    
    def _update_pattern(self, pattern: Dict[str, Any], response: str, source: str):
        """Update learned patterns"""
        pattern_key = self._pattern_key(pattern)
        
        if pattern_key not in self.patterns["query_patterns"]:
            self.patterns["query_patterns"][pattern_key] = {
                "count": 1,
                "sources": [source],
                "response_samples": [response[:200]],  # First 200 chars
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
        else:
            pattern_data = self.patterns["query_patterns"][pattern_key]
            pattern_data["count"] += 1
            pattern_data["last_seen"] = datetime.now().isoformat()
            
            if source not in pattern_data["sources"]:
                pattern_data["sources"].append(source)
            
            # Keep last 5 response samples
            pattern_data["response_samples"].append(response[:200])
            if len(pattern_data["response_samples"]) > 5:
                pattern_data["response_samples"] = pattern_data["response_samples"][-5:]
    
    def _pattern_key(self, pattern: Dict[str, Any]) -> str:
        """Generate key for pattern"""
        key_parts = []
        if pattern.get("question_type"):
            key_parts.append(pattern["question_type"])
        if pattern.get("entities"):
            key_parts.extend(pattern["entities"][:3])  # First 3 entities
        return "_".join(key_parts) if key_parts else "general"
    
    def _update_source_effectiveness(self, source: str, response: str, user_feedback: Optional[float]):
        """Update source effectiveness metrics"""
        if source not in self.success_metrics["source_success_rates"]:
            self.success_metrics["source_success_rates"][source] = {
                "total_uses": 0,
                "successful_uses": 0,
                "average_quality": 0.0,
                "feedback_sum": 0.0,
                "feedback_count": 0
            }
        
        metrics = self.success_metrics["source_success_rates"][source]
        metrics["total_uses"] += 1
        
        # Assess if response was successful (non-empty, meaningful)
        is_successful = len(response) > 20 and not response.startswith("I'm processing")
        if is_successful:
            metrics["successful_uses"] += 1
        
        # Update feedback
        if user_feedback is not None:
            metrics["feedback_sum"] += user_feedback
            metrics["feedback_count"] += 1
            metrics["average_quality"] = metrics["feedback_sum"] / metrics["feedback_count"]
    
    def _assess_response_quality(self, response: str, query: str) -> float:
        """Assess response quality (0.0 to 1.0)"""
        score = 0.0
        
        # Length check (too short = low quality)
        if len(response) < 10:
            return 0.1
        
        # Relevance check (response should relate to query)
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        overlap = len(query_words & response_words)
        if len(query_words) > 0:
            relevance = min(1.0, overlap / len(query_words))
            score += relevance * 0.4
        
        # Informativeness (longer, detailed responses = better)
        if len(response) > 100:
            score += 0.3
        elif len(response) > 50:
            score += 0.2
        
        # Structure (has formatting, lists, etc.)
        if any(marker in response for marker in ["\n", "-", "•", "1.", "2."]):
            score += 0.2
        
        # Source indication (mentions source = more credible)
        if any(word in response.lower() for word in ["source:", "according to", "from"]):
            score += 0.1
        
        return min(1.0, score)
    
    def _update_quality_metrics(self, query: str, response: str, quality_score: float, source: str):
        """Update quality metrics"""
        query_hash = hashlib.md5(query.lower().encode()).hexdigest()[:8]
        
        self.success_metrics["response_quality_scores"][query_hash] = {
            "query": query[:100],  # First 100 chars
            "quality_score": quality_score,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        
        # Keep only last 1000 quality scores
        if len(self.success_metrics["response_quality_scores"]) > 1000:
            oldest = min(
                self.success_metrics["response_quality_scores"].keys(),
                key=lambda k: self.success_metrics["response_quality_scores"][k]["timestamp"]
            )
            del self.success_metrics["response_quality_scores"][oldest]
    
    def get_best_source(self, query: str) -> Optional[str]:
        """Get best source for a query based on learned patterns"""
        pattern = self._extract_query_pattern(query)
        if not pattern:
            return None
        
        pattern_key = self._pattern_key(pattern)
        
        # Check if we have patterns for this
        if pattern_key in self.patterns["query_patterns"]:
            pattern_data = self.patterns["query_patterns"][pattern_key]
            sources = pattern_data.get("sources", [])
            
            if sources:
                # Return most used source for this pattern
                from collections import Counter
                source_counts = Counter(sources)
                return source_counts.most_common(1)[0][0]
        
        # Fallback: use source with highest success rate
        source_rates = self.success_metrics.get("source_success_rates", {})
        if source_rates:
            best_source = max(
                source_rates.items(),
                key=lambda x: x[1].get("successful_uses", 0) / max(x[1].get("total_uses", 1), 1)
            )
            return best_source[0]
        
        return None
    
    def get_learned_response_template(self, query: str) -> Optional[str]:
        """Get learned response template for similar queries"""
        pattern = self._extract_query_pattern(query)
        if not pattern:
            return None
        
        pattern_key = self._pattern_key(pattern)
        
        if pattern_key in self.patterns["query_patterns"]:
            samples = self.patterns["query_patterns"][pattern_key].get("response_samples", [])
            if samples:
                # Return most recent sample
                return samples[-1]
        
        return None
    
    def _save_learning_data(self):
        """Save learning data to disk"""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
            
            with open(self.success_file, 'w', encoding='utf-8') as f:
                json.dump(self.success_metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            **self.stats,
            "patterns_count": len(self.patterns.get("query_patterns", {})),
            "sources_tracked": len(self.success_metrics.get("source_success_rates", {})),
            "quality_scores_count": len(self.success_metrics.get("response_quality_scores", {}))
        }


# Global instance
_real_time_learner = None

def get_real_time_learner() -> RealTimeLearner:
    """Get or create real-time learner"""
    global _real_time_learner
    if _real_time_learner is None:
        _real_time_learner = RealTimeLearner()
    return _real_time_learner

