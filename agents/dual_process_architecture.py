#!/usr/bin/env python3
"""
System 1 + System 2 Architecture for FAME
Inspired by human dual-process cognition (Kahneman)
"""

import logging
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SystemResponse:
    """Response from System 1 or System 2"""
    answer: str
    confidence: float
    latency_ms: float
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = None


class FastIntuitiveModel:
    """
    System 1: Fast, intuitive, pattern-matching
    Quick responses based on heuristics and pattern recognition
    """
    
    def __init__(self):
        self.pattern_cache: Dict[str, Any] = {}
        self.confidence_threshold = 0.8  # High confidence needed for System 1
        
    def process(self, problem: str, context: Optional[Dict[str, Any]] = None) -> SystemResponse:
        """
        Fast pattern-matching and heuristic-based processing
        
        Args:
            problem: Problem to solve
            context: Optional context
            
        Returns:
            SystemResponse with answer and confidence
        """
        start_time = time.time()
        
        # Check pattern cache
        if problem in self.pattern_cache:
            cached = self.pattern_cache[problem]
            return SystemResponse(
                answer=cached["answer"],
                confidence=cached["confidence"],
                latency_ms=(time.time() - start_time) * 1000,
                reasoning="Pattern-matched from cache",
                metadata={"source": "cache"}
            )
        
        # Quick pattern matching
        answer, confidence = self._pattern_match(problem)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Cache result
        if confidence >= 0.7:
            self.pattern_cache[problem] = {
                "answer": answer,
                "confidence": confidence
            }
        
        return SystemResponse(
            answer=answer,
            confidence=confidence,
            latency_ms=latency_ms,
            reasoning="Fast pattern matching",
            metadata={"source": "system1"}
        )
    
    def _pattern_match(self, problem: str) -> tuple[str, float]:
        """Quick pattern matching (simplified)"""
        problem_lower = problem.lower()
        
        # Simple keyword-based matching
        patterns = {
            ("hello", "hi", "hey"): ("Hello! How can I help you today?", 0.95),
            ("time", "what time"): ("I can check the current time for you.", 0.85),
            ("price", "cost", "how much"): ("I can look up current prices.", 0.80),
            ("weather", "temperature"): ("I can provide weather information.", 0.85),
        }
        
        for keywords, (answer, confidence) in patterns.items():
            if any(kw in problem_lower for kw in keywords):
                return answer, confidence
                
        # Default: low confidence for unknown patterns
        return "I'm processing your request...", 0.3
    
    def confidence_estimate(self, problem: str) -> float:
        """Estimate confidence for System 1 response"""
        _, confidence = self._pattern_match(problem)
        return confidence


class SlowReasoningModel:
    """
    System 2: Slow, deliberate, analytical reasoning
    Uses Tree-of-Thoughts, MCTS, or other advanced reasoning
    """
    
    def __init__(self, use_tot: bool = True, use_mcts: bool = True):
        self.use_tot = use_tot
        self.use_mcts = use_mcts
        
        if use_tot:
            try:
                from agents.tree_of_thoughts import TreeOfThoughts
                self.tot = TreeOfThoughts(breadth=5, max_depth=3)
            except ImportError:
                logger.warning("TreeOfThoughts not available")
                self.tot = None
        else:
            self.tot = None
            
        if use_mcts:
            try:
                from agents.mcts_decision_maker import MCTSDecisionMaker
                self.mcts = MCTSDecisionMaker(simulation_budget=500)
            except ImportError:
                logger.warning("MCTSDecisionMaker not available")
                self.mcts = None
        else:
            self.mcts = None
    
    def deliberate(self, problem: str, intuitive_answer: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None) -> SystemResponse:
        """
        Deliberate reasoning using System 2
        
        Args:
            problem: Problem to solve
            intuitive_answer: Answer from System 1 (for comparison)
            context: Optional context
            
        Returns:
            SystemResponse with carefully reasoned answer
        """
        start_time = time.time()
        
        # Use Tree-of-Thoughts for complex reasoning
        if self.tot and self._is_complex(problem):
            result = self.tot.search(problem, context)
            
            best_thought = result["best_thoughts"][0] if result["best_thoughts"] else None
            
            if best_thought:
                answer = best_thought["content"]
                confidence = best_thought["confidence"]
                reasoning = f"Tree-of-Thoughts reasoning (depth {best_thought['depth']})"
            else:
                answer = intuitive_answer or "I need more time to think about this."
                confidence = 0.6
                reasoning = "ToT search completed but no clear answer"
        else:
            # Fallback to rule-based reasoning
            answer, confidence = self._rule_based_reasoning(problem, context)
            reasoning = "Rule-based reasoning"
        
        latency_ms = (time.time() - start_time) * 1000
        
        return SystemResponse(
            answer=answer,
            confidence=confidence,
            latency_ms=latency_ms,
            reasoning=reasoning,
            metadata={
                "source": "system2",
                "used_tot": self.tot is not None,
                "intuitive_answer": intuitive_answer
            }
        )
    
    def _is_complex(self, problem: str) -> bool:
        """Determine if problem requires complex reasoning"""
        complex_keywords = [
            "analyze", "compare", "explain", "why", "how", "predict",
            "strategy", "plan", "design", "evaluate"
        ]
        return any(kw in problem.lower() for kw in complex_keywords)
    
    def _rule_based_reasoning(self, problem: str, 
                             context: Optional[Dict[str, Any]]) -> tuple[str, float]:
        """Rule-based reasoning fallback"""
        # Simplified rule-based reasoning
        return "I'm carefully considering your question...", 0.7


class DualProcessArchitecture:
    """
    Dual-process architecture combining System 1 (fast) and System 2 (slow)
    """
    
    def __init__(self, confidence_threshold: float = 0.8):
        """
        Initialize dual-process architecture
        
        Args:
            confidence_threshold: Threshold below which System 2 is engaged
        """
        self.system1 = FastIntuitiveModel()
        self.system2 = SlowReasoningModel()
        self.confidence_threshold = confidence_threshold
        
    def decide(self, problem: str, context: Optional[Dict[str, Any]] = None) -> SystemResponse:
        """
        Decide using System 1 or System 2
        
        Args:
            problem: Problem to solve
            context: Optional context
            
        Returns:
            SystemResponse from appropriate system
        """
        # System 1: Quick assessment
        start_time = time.time()
        intuitive_response = self.system1.process(problem, context)
        
        confidence = intuitive_response.confidence
        
        logger.debug(f"System 1 response: confidence={confidence:.2f}, latency={intuitive_response.latency_ms:.1f}ms")
        
        # Decision point: Engage System 2 if confidence too low
        if confidence < self.confidence_threshold:
            logger.debug(f"System 1 confidence {confidence:.2f} < threshold {self.confidence_threshold}, engaging System 2")
            
            # System 2: Deliberate reasoning
            deliberate_response = self.system2.deliberate(
                problem, 
                intuitive_response.answer,
                context
            )
            
            # Compare responses
            if deliberate_response.confidence > intuitive_response.confidence:
                logger.debug(f"System 2 response better (conf: {deliberate_response.confidence:.2f}), using it")
                return deliberate_response
            else:
                logger.debug(f"System 1 response sufficient, using it")
                return intuitive_response
        else:
            # System 1 response is sufficient
            logger.debug(f"System 1 confidence {confidence:.2f} >= threshold, using fast response")
            return intuitive_response

