#!/usr/bin/env python3
"""
FAME AGI - Confidence Thresholding & Safety Layer
Gates actions, prevents hallucinations, triggers verification loops
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels"""
    VERY_HIGH = "very_high"  # > 0.9
    HIGH = "high"  # 0.7-0.9
    MEDIUM = "medium"  # 0.5-0.7
    LOW = "low"  # 0.3-0.5
    VERY_LOW = "very_low"  # < 0.3


class ConfidenceThresholding:
    """
    Confidence-based safety layer with hallucination prevention and verification loops.
    Gates actions and triggers recursive improvement.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Thresholds
        self.thresholds = {
            "action_gate": 0.6,  # Minimum confidence to take action
            "verification_trigger": 0.7,  # Trigger verification if below
            "hallucination_detection": 0.5,  # Below this = potential hallucination
            "reject_threshold": 0.3,  # Below this = reject
            "additional_search": 0.6  # Trigger additional search if below
        }
        
        # Verification settings
        self.max_verification_loops = 3
        self.verification_improvement_threshold = 0.1  # Minimum improvement needed
    
    def evaluate_confidence(self, confidence: float, response: str,
                           sources: List[str], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate confidence and determine actions.
        Returns decision with reasoning.
        """
        context = context or {}
        confidence_level = self._classify_confidence(confidence)
        
        decision = {
            "confidence": confidence,
            "level": confidence_level.value,
            "action": "accept",
            "requires_verification": False,
            "requires_additional_search": False,
            "should_reject": False,
            "reasoning": "",
            "suggested_actions": []
        }
        
        # Very low confidence - reject
        if confidence < self.thresholds["reject_threshold"]:
            decision["action"] = "reject"
            decision["should_reject"] = True
            decision["reasoning"] = f"Confidence {confidence:.2f} below rejection threshold {self.thresholds['reject_threshold']}"
            decision["suggested_actions"] = ["request_clarification", "ask_for_more_context"]
            return decision
        
        # Low confidence - trigger verification
        if confidence < self.thresholds["verification_trigger"]:
            decision["requires_verification"] = True
            decision["reasoning"] = f"Confidence {confidence:.2f} below verification threshold"
            decision["suggested_actions"].append("verify_with_additional_sources")
        
        # Medium confidence - check for hallucination
        if confidence < self.thresholds["hallucination_detection"]:
            hallucination_risk = self._detect_hallucination_risk(response, sources)
            if hallucination_risk:
                decision["requires_verification"] = True
                decision["suggested_actions"].append("hallucination_check")
                decision["reasoning"] += " Potential hallucination detected."
        
        # Below action gate - trigger additional search
        if confidence < self.thresholds["additional_search"]:
            decision["requires_additional_search"] = True
            decision["suggested_actions"].append("web_search")
            decision["reasoning"] += " Low confidence - triggering additional search."
        
        # Below action gate - don't take action
        if confidence < self.thresholds["action_gate"]:
            decision["action"] = "verify_first"
            decision["reasoning"] += f" Confidence {confidence:.2f} below action gate {self.thresholds['action_gate']}"
        
        return decision
    
    def should_trigger_verification(self, confidence: float, response: str,
                                   sources: List[str]) -> bool:
        """Determine if verification loop should be triggered"""
        if confidence < self.thresholds["verification_trigger"]:
            return True
        
        if confidence < self.thresholds["hallucination_detection"]:
            if self._detect_hallucination_risk(response, sources):
                return True
        
        return False
    
    def should_reject(self, confidence: float) -> bool:
        """Determine if response should be rejected"""
        return confidence < self.thresholds["reject_threshold"]
    
    def should_trigger_additional_search(self, confidence: float) -> bool:
        """Determine if additional search is needed"""
        return confidence < self.thresholds["additional_search"]
    
    def can_take_action(self, confidence: float) -> bool:
        """Determine if action can be taken"""
        return confidence >= self.thresholds["action_gate"]
    
    def _classify_confidence(self, confidence: float) -> ConfidenceLevel:
        """Classify confidence into level"""
        if confidence >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.5:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.3:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _detect_hallucination_risk(self, response: str, sources: List[str]) -> bool:
        """Detect potential hallucination"""
        # High confidence but no sources = risk
        if not sources or len(sources) == 0:
            return True
        
        # Very long response with few sources = risk
        if len(response.split()) > 200 and len(sources) < 2:
            return True
        
        # Response contains specific numbers/dates but no source = risk
        import re
        numbers = re.findall(r'\d+', response)
        if len(numbers) > 3 and "source" not in response.lower():
            return True
        
        return False
    
    def verify_response(self, response: str, original_confidence: float,
                       verification_sources: List[str]) -> Tuple[float, str]:
        """
        Verify response with additional sources.
        Returns improved confidence and verified response.
        """
        # Simple verification: if sources match, increase confidence
        verified_response = response
        new_confidence = original_confidence
        
        if verification_sources:
            # Check if response is consistent with sources
            consistency_score = self._check_consistency(response, verification_sources)
            
            if consistency_score > 0.7:
                new_confidence = min(1.0, original_confidence + 0.2)
                verified_response = f"{response}\n\n[Verified with {len(verification_sources)} additional sources]"
            elif consistency_score < 0.3:
                new_confidence = max(0.0, original_confidence - 0.2)
                verified_response = f"{response}\n\n[Warning: Inconsistency detected with sources]"
        
        return new_confidence, verified_response
    
    def _check_consistency(self, response: str, sources: List[str]) -> float:
        """Check consistency between response and sources"""
        # Simple keyword overlap check
        response_words = set(response.lower().split())
        source_text = " ".join(sources).lower()
        source_words = set(source_text.split())
        
        if not response_words or not source_words:
            return 0.5
        
        overlap = len(response_words.intersection(source_words))
        total = len(response_words.union(source_words))
        
        return overlap / total if total > 0 else 0.0
    
    def recursive_improvement(self, response: str, confidence: float,
                             sources: List[str], max_iterations: int = 3) -> Tuple[str, float]:
        """
        Recursive improvement loop until confidence threshold met.
        """
        current_response = response
        current_confidence = confidence
        iteration = 0
        
        while iteration < max_iterations:
            decision = self.evaluate_confidence(current_confidence, current_response, sources)
            
            # If confidence is acceptable, return
            if decision["action"] == "accept" and not decision["requires_verification"]:
                return current_response, current_confidence
            
            # If should reject, return with low confidence
            if decision["should_reject"]:
                return current_response, current_confidence
            
            # Trigger verification
            if decision["requires_verification"]:
                # In real implementation, would fetch additional sources
                verification_sources = sources  # Placeholder
                current_confidence, current_response = self.verify_response(
                    current_response, current_confidence, verification_sources
                )
            
            # Trigger additional search
            if decision["requires_additional_search"]:
                # In real implementation, would perform additional web search
                # For now, just mark as improved
                current_confidence = min(1.0, current_confidence + 0.1)
            
            iteration += 1
        
        return current_response, current_confidence

