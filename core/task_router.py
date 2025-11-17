#!/usr/bin/env python3
"""
FAME AGI - Task & Intent Router
The heart of FAME: Classifies intents and routes to appropriate executors
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """Intent classification types"""
    MEMORY_RETRIEVAL = "memory_retrieval"
    WEB_SEARCH = "web_search"
    KNOWLEDGE_FUSION = "knowledge_fusion"
    LLM_GENERATION = "llm_generation"
    AGENT_PLAN = "agent_plan"
    CODE_EXECUTION = "code_execution"
    DATA_ANALYSIS = "data_analysis"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """Result of intent classification"""
    intent: IntentType
    confidence: float
    slots: Dict[str, Any]
    reasoning: str
    requires_planning: bool
    estimated_complexity: int  # 1-10 scale


@dataclass
class ExecutionPlan:
    """Final execution plan with executor selection"""
    intent: IntentType
    executors: List[str]  # Ordered list of executors to try
    confidence_threshold: float
    requires_verification: bool
    max_iterations: int
    fallback_chain: List[str]


class TaskRouter:
    """
    Core intent router for FAME AGI.
    Classifies user input and determines execution strategy.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.confidence_thresholds = {
            IntentType.MEMORY_RETRIEVAL: 0.7,
            IntentType.WEB_SEARCH: 0.6,
            IntentType.KNOWLEDGE_FUSION: 0.75,
            IntentType.LLM_GENERATION: 0.5,
            IntentType.AGENT_PLAN: 0.8,
            IntentType.CODE_EXECUTION: 0.85,
            IntentType.DATA_ANALYSIS: 0.7
        }
        
        # Pattern matchers
        self.memory_patterns = [
            r"remember|recall|what did|tell me about|do you know",
            r"previous|earlier|before|last time",
            r"history|past|conversation"
        ]
        
        self.web_search_patterns = [
            r"current|latest|recent|now|today|what is|who is|where is",
            r"price|market|news|trend|update",
            r"search|find|look up|google"
        ]
        
        self.planning_patterns = [
            r"plan|strategy|steps|how to|break down|analyze",
            r"complex|multiple|several|various",
            r"create|build|develop|design|implement"
        ]
        
        self.code_patterns = [
            r"code|script|function|program|algorithm",
            r"write|generate|create.*code|implement.*function"
        ]
        
        self.analysis_patterns = [
            r"analyze|analysis|compare|evaluate|assess",
            r"data|dataset|statistics|metrics"
        ]
    
    def intent_classifier(self, user_input: str, context: Optional[List[Dict[str, str]]] = None) -> IntentResult:
        """
        Classify user input into intent type with confidence.
        This is the core decision-making function.
        """
        user_input_lower = user_input.lower().strip()
        context = context or []
        
        # Extract slots
        slots = self._extract_slots(user_input)
        
        # Score each intent type
        scores = {}
        
        # Memory retrieval
        memory_score = self._score_patterns(user_input_lower, self.memory_patterns)
        if any("remember" in msg.get("content", "").lower() for msg in context[-3:]):
            memory_score += 0.3
        scores[IntentType.MEMORY_RETRIEVAL] = memory_score
        
        # Web search
        web_score = self._score_patterns(user_input_lower, self.web_search_patterns)
        if any(word in user_input_lower for word in ["current", "latest", "now", "today", "price"]):
            web_score += 0.4
        scores[IntentType.WEB_SEARCH] = web_score
        
        # Planning
        plan_score = self._score_patterns(user_input_lower, self.planning_patterns)
        if len(user_input.split()) > 15:  # Longer queries often need planning
            plan_score += 0.2
        scores[IntentType.AGENT_PLAN] = plan_score
        
        # Code execution
        code_score = self._score_patterns(user_input_lower, self.code_patterns)
        scores[IntentType.CODE_EXECUTION] = code_score
        
        # Data analysis
        analysis_score = self._score_patterns(user_input_lower, self.analysis_patterns)
        scores[IntentType.DATA_ANALYSIS] = analysis_score
        
        # Knowledge fusion (combines memory + web + LLM)
        fusion_score = (memory_score * 0.3 + web_score * 0.3 + 0.4) if (memory_score > 0.3 or web_score > 0.3) else 0.0
        scores[IntentType.KNOWLEDGE_FUSION] = fusion_score
        
        # LLM generation (fallback for creative/complex queries)
        llm_score = 0.5  # Base score
        if plan_score > 0.5 or code_score > 0.5:
            llm_score = max(plan_score, code_score) * 0.8
        if memory_score < 0.3 and web_score < 0.3:
            llm_score += 0.3  # No clear pattern = likely needs LLM
        scores[IntentType.LLM_GENERATION] = llm_score
        
        # Select best intent
        best_intent = max(scores.items(), key=lambda x: x[1])
        intent_type, confidence = best_intent
        
        # Determine complexity
        complexity = self._estimate_complexity(user_input, intent_type, slots)
        
        # Determine if planning is required
        requires_planning = (
            intent_type == IntentType.AGENT_PLAN or
            complexity > 5 or
            confidence < 0.6
        )
        
        reasoning = f"Classified as {intent_type.value} (confidence: {confidence:.2f}) based on patterns and context"
        
        return IntentResult(
            intent=intent_type,
            confidence=confidence,
            slots=slots,
            reasoning=reasoning,
            requires_planning=requires_planning,
            estimated_complexity=complexity
        )
    
    def should_search_memory(self, intent: IntentResult, context: Optional[List[Dict[str, str]]] = None) -> bool:
        """Determine if memory search is needed"""
        if intent.intent == IntentType.MEMORY_RETRIEVAL:
            return True
        if intent.intent == IntentType.KNOWLEDGE_FUSION:
            return True
        if intent.confidence < 0.6:  # Low confidence = check memory first
            return True
        return False
    
    def should_query_web(self, intent: IntentResult) -> bool:
        """Determine if web search is needed"""
        if intent.intent == IntentType.WEB_SEARCH:
            return True
        if intent.intent == IntentType.KNOWLEDGE_FUSION:
            return True
        if "current" in intent.slots.get("keywords", []):
            return True
        return False
    
    def should_call_llm_cloud(self, intent: IntentResult, complexity: Optional[int] = None) -> bool:
        """Determine if cloud LLM should be called"""
        complexity = complexity or intent.estimated_complexity
        
        if intent.intent == IntentType.LLM_GENERATION:
            return True
        if intent.intent == IntentType.AGENT_PLAN:
            return True
        if intent.intent == IntentType.CODE_EXECUTION:
            return True
        if complexity > 6:  # High complexity needs cloud LLM
            return True
        if intent.confidence < 0.5:  # Low confidence = use LLM
            return True
        return False
    
    def should_use_local_model(self, intent: IntentResult, latency_sensitive: bool = False) -> bool:
        """Determine if local model should be used"""
        if latency_sensitive and intent.estimated_complexity < 4:
            return True
        if intent.intent == IntentType.MEMORY_RETRIEVAL and intent.confidence > 0.8:
            return True  # Simple memory queries can use local
        return False
    
    def produce_final_plan(self, intent: IntentResult, context: Optional[List[Dict[str, str]]] = None) -> ExecutionPlan:
        """
        Produce final execution plan with executor chain.
        This is where FAME decides HOW to execute.
        """
        executors = []
        fallback_chain = []
        
        # Build executor chain based on intent
        if self.should_search_memory(intent, context):
            executors.append("memory_agent")
            fallback_chain.append("vector_search")
        
        if self.should_query_web(intent):
            executors.append("web_agent")
            fallback_chain.append("serpapi")
            fallback_chain.append("direct_scrape")
        
        if self.should_call_llm_cloud(intent):
            executors.append("cloud_llm")
            fallback_chain.append("openai")
            fallback_chain.append("google_ai")
        
        if self.should_use_local_model(intent):
            executors.append("local_llm")
            fallback_chain.append("transformers")
        
        # Always add fusion agent at the end
        if len(executors) > 1:
            executors.append("fusion_agent")
        
        # If no executors selected, default to LLM
        if not executors:
            executors = ["cloud_llm", "local_llm"]
            fallback_chain = ["openai", "google_ai", "transformers"]
        
        # Determine confidence threshold
        confidence_threshold = self.confidence_thresholds.get(intent.intent, 0.6)
        
        # Determine if verification is needed
        requires_verification = (
            intent.estimated_complexity > 6 or
            intent.confidence < 0.7 or
            intent.intent == IntentType.CODE_EXECUTION
        )
        
        # Determine max iterations (for recursive improvement)
        max_iterations = 1
        if requires_verification:
            max_iterations = 3
        if intent.estimated_complexity > 8:
            max_iterations = 5
        
        return ExecutionPlan(
            intent=intent.intent,
            executors=executors,
            confidence_threshold=confidence_threshold,
            requires_verification=requires_verification,
            max_iterations=max_iterations,
            fallback_chain=fallback_chain
        )
    
    def _score_patterns(self, text: str, patterns: List[str]) -> float:
        """Score text against pattern list"""
        matches = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        if not patterns:
            return 0.0
        return min(1.0, matches / len(patterns) + (matches * 0.2))
    
    def _extract_slots(self, text: str) -> Dict[str, Any]:
        """Extract semantic slots from text"""
        slots = {
            "keywords": [],
            "entities": [],
            "time_references": [],
            "numbers": []
        }
        
        # Extract keywords (important words)
        words = text.split()
        important_words = [w for w in words if len(w) > 4 and w.lower() not in ["what", "when", "where", "which", "about"]]
        slots["keywords"] = important_words[:5]
        
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', text)
        slots["numbers"] = [float(n) for n in numbers[:5]]
        
        # Extract time references
        time_refs = re.findall(r'\b(today|yesterday|tomorrow|now|recent|latest|current)\b', text, re.IGNORECASE)
        slots["time_references"] = time_refs
        
        # Simple entity extraction (can be enhanced with NER)
        # Look for capitalized words (potential entities)
        entities = re.findall(r'\b[A-Z][a-z]+\b', text)
        slots["entities"] = entities[:5]
        
        return slots
    
    def _estimate_complexity(self, text: str, intent: IntentType, slots: Dict[str, Any]) -> int:
        """Estimate query complexity (1-10 scale)"""
        complexity = 1
        
        # Base complexity by intent
        intent_complexity = {
            IntentType.MEMORY_RETRIEVAL: 2,
            IntentType.WEB_SEARCH: 3,
            IntentType.KNOWLEDGE_FUSION: 6,
            IntentType.LLM_GENERATION: 5,
            IntentType.AGENT_PLAN: 8,
            IntentType.CODE_EXECUTION: 7,
            IntentType.DATA_ANALYSIS: 6
        }
        complexity = intent_complexity.get(intent, 5)
        
        # Adjust based on text length
        word_count = len(text.split())
        if word_count > 50:
            complexity += 2
        elif word_count > 20:
            complexity += 1
        
        # Adjust based on number of entities
        if len(slots.get("entities", [])) > 3:
            complexity += 1
        
        # Adjust based on multiple questions
        question_count = text.count("?")
        if question_count > 1:
            complexity += 1
        
        return min(10, complexity)


# Singleton instance
_task_router: Optional[TaskRouter] = None

def get_task_router(config: Optional[Dict[str, Any]] = None) -> TaskRouter:
    """Get or create task router instance"""
    global _task_router
    if _task_router is None:
        _task_router = TaskRouter(config)
    return _task_router

