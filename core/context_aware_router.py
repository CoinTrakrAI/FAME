#!/usr/bin/env python3
"""
Context-Aware Intent Router
Enhanced intent router that maintains conversation context
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging
from collections import deque

logger = logging.getLogger(__name__)


class ContextAwareIntentRouter:
    """Enhanced intent router that maintains conversation context"""
    
    def __init__(self, max_context_length: int = 5):
        self.max_context = max_context_length
        self.conversation_context = deque(maxlen=max_context_length)
        self.logger = logging.getLogger(__name__)
        
        # Contextual intent patterns
        self.contextual_patterns = {
            "affirmative_followup": [
                (r"\b(yes|yeah|yep|sure|ok|okay|please do|go ahead)\b", 0.9),
                (r"\b(absolutely|definitely|certainly|of course)\b", 0.95),
                (r"\b(yep|yup|uh huh|mm hmm)\b", 0.85),
                (r"^yes$", 0.95),  # Exact match for "yes" gets higher confidence
                (r"^yeah$", 0.95),
                (r"^ok$", 0.9),
                (r"^okay$", 0.9)
            ],
            "negative_followup": [
                (r"\b(no|nope|nah|not really|don't)\b", 0.9),
                (r"\b(no thanks|no thank you|not now)\b", 0.95),
                (r"^no$", 0.95)  # Exact match for "no"
            ],
            "technical_build": [
                (r"build.*program", 0.8),
                (r"create.*executable", 0.9),
                (r"make.*exe", 0.85),
                (r"convert.*executable", 0.8),
                (r"build.*script", 0.85),
                (r"create.*build", 0.9)
            ]
        }
        
        # Compile patterns for performance
        self.compiled_patterns = {}
        for intent, patterns in self.contextual_patterns.items():
            self.compiled_patterns[intent] = [
                (re.compile(pattern, re.IGNORECASE), confidence) 
                for pattern, confidence in patterns
            ]
    
    def add_to_context(self, user_input: str, ai_response: str, intent: str):
        """Add conversation exchange to context"""
        self.conversation_context.append({
            'user': user_input,
            'ai': ai_response,
            'intent': intent,
            'timestamp': datetime.now()
        })
    
    def get_recent_intents(self, count: int = 3) -> List[str]:
        """Get recent conversation intents"""
        return [exchange['intent'] for exchange in 
                list(self.conversation_context)[-count:]]
    
    def is_affirmative_followup(self, user_input: str) -> Tuple[bool, float, Optional[str]]:
        """
        Check if input is affirmative in context
        
        Returns: (is_affirmative, confidence, expected_response_type)
        """
        user_lower = user_input.lower().strip()
        
        # Check for affirmative patterns
        max_confidence = 0.0
        for pattern, base_confidence in self.compiled_patterns["affirmative_followup"]:
            if pattern.search(user_lower):
                max_confidence = max(max_confidence, base_confidence)
        
        if max_confidence > 0:
            # Boost confidence based on recent context
            context_boost, expected_type = self._calculate_context_boost()
            final_confidence = min(1.0, max_confidence + context_boost)
            return True, final_confidence, expected_type
        
        return False, 0.0, None
    
    def is_negative_followup(self, user_input: str) -> Tuple[bool, float]:
        """Check if input is negative in context"""
        user_lower = user_input.lower().strip()
        
        for pattern, base_confidence in self.compiled_patterns["negative_followup"]:
            if pattern.search(user_lower):
                context_boost = self._calculate_context_boost()[0]
                final_confidence = min(1.0, base_confidence + context_boost)
                return True, final_confidence
        
        return False, 0.0
    
    def _calculate_context_boost(self) -> Tuple[float, Optional[str]]:
        """
        Calculate confidence boost based on conversation context
        
        Returns: (boost_value, expected_response_type)
        """
        if not self.conversation_context:
            return 0.0, None
        
        recent_exchanges = list(self.conversation_context)[-2:]  # Last 2 exchanges
        
        # Check if recent context suggests technical follow-up
        technical_indicators = [
            exchange for exchange in recent_exchanges 
            if exchange['intent'] in ['technical', 'code_generation', 'build_request']
        ]
        
        # Check last AI response for context clues
        last_exchange = recent_exchanges[-1] if recent_exchanges else None
        if last_exchange:
            last_ai_response = last_exchange['ai'].lower()
            
            # Check for build/executable context
            if any(keyword in last_ai_response for keyword in 
                   ['executable', 'pyinstaller', 'build script', '.exe', 'build', 'create a build']):
                return 0.4, 'build_instructions'  # Strong boost for build context
            
            # Check for code generation context
            if any(keyword in last_ai_response for keyword in 
                   ['code', 'program', 'script', 'function', 'write', 'create']):
                return 0.3, 'code_generation'  # Moderate boost for code context
            
            # Check for question context (asking if user wants something)
            if any(keyword in last_ai_response for keyword in 
                   ['would you like', 'do you want', 'should i', 'can i help']):
                return 0.3, 'affirmative_response'  # Boost for question follow-up
        
        if len(technical_indicators) >= 1:
            return 0.4, 'technical'  # Strong boost for technical context
        
        return 0.1, None  # Small boost for any context
    
    def get_expected_response_type(self) -> Optional[str]:
        """Determine what type of response is expected based on context"""
        if not self.conversation_context:
            return None
        
        last_exchange = self.conversation_context[-1]
        last_ai_response = last_exchange['ai'].lower()
        
        # Check for build/executable context
        if any(keyword in last_ai_response for keyword in 
               ['executable', 'pyinstaller', 'build script', '.exe', 'build', 'create a build']):
            return 'build_instructions'
        
        # Check for code generation context
        if any(keyword in last_ai_response for keyword in 
               ['code', 'program', 'script', 'function', 'write', 'create']):
            return 'code_generation'
        
        # Check for question context
        if any(keyword in last_ai_response for keyword in 
               ['would you like', 'do you want', 'should i', 'can i help', 'help you']):
            return 'affirmative_response'
        
        return None


# Singleton instance
_context_router: Optional[ContextAwareIntentRouter] = None


def get_context_router() -> ContextAwareIntentRouter:
    """Get or create context router instance"""
    global _context_router
    if _context_router is None:
        _context_router = ContextAwareIntentRouter()
    return _context_router

