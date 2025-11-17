#!/usr/bin/env python3
"""
Enhanced Intent Recognition with Context Awareness
Immediate patch for intent recognition
"""

import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def enhanced_recognize_intent(user_input: str, context: List[Dict] = None) -> Dict:
    """Enhanced intent recognition with context awareness"""
    
    user_clean = user_input.lower().strip()
    
    # CRITICAL: Handle affirmative responses first
    try:
        from hotfixes.critical_context_fix import critical_context_fix
        if critical_context_fix.is_affirmative_followup(user_input):
            last_intent = critical_context_fix.last_intent
            if last_intent in ['technical', 'build_request', 'code_generation', 'wifi_security']:
                return {
                    'intent': 'affirmative_followup', 
                    'confidence': 0.95,
                    'context': last_intent,
                    'should_search': False
                }
    except Exception as e:
        logger.debug(f"Critical context fix check failed: {e}")
    
    # Check for simple affirmative patterns (prevent band confusion)
    affirmative_patterns = [
        r'^yes$', r'^yeah$', r'^yep$', r'^sure$', r'^ok$', r'^okay$',
        r'^please do$', r'^go ahead$', r'^absolutely$', r'^definitely$'
    ]
    
    for pattern in affirmative_patterns:
        if re.match(pattern, user_clean):
            return {
                'intent': 'affirmative',
                'confidence': 0.9,
                'should_search': False
            }
    
    # Return None to continue with normal intent recognition
    return None

