#!/usr/bin/env python3
"""
Debug Conversation Flow
Enhanced logging for debugging context issues
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def debug_conversation_flow(user_input: str, ai_response: str, intent: str):
    """Debug conversation flow to identify context issues"""
    try:
        from hotfixes.critical_context_fix import critical_context_fix
        
        print(f"\n🔍 DEBUG CONVERSATION:")
        print(f"   User: {user_input}")
        print(f"   Intent: {intent}")
        print(f"   Response Preview: {ai_response[:100]}...")
        print(f"   Context History: {[ex.get('intent', 'unknown') for ex in critical_context_fix.conversation_history]}")
        
        # Check for problematic patterns
        if intent == 'general' and len(user_input) < 10:
            print("   ⚠️  WARNING: Short input might be misclassified!")
        
        # Check if affirmative was missed
        if user_input.lower().strip() in ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay']:
            if intent != 'affirmative_followup' and intent != 'build_instructions':
                print("   ⚠️  WARNING: Affirmative response might be misclassified!")
    except Exception as e:
        logger.debug(f"Debug conversation flow failed: {e}")

