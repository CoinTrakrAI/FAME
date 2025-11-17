#!/usr/bin/env python3
"""
Conversation Logger
Log conversation context for debugging
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConversationLogger:
    """Log conversation context for debugging"""
    
    def __init__(self):
        self.logger = logging.getLogger('conversation.context')
        
    def log_exchange(self, user_input: str, ai_response: str, intent: str, confidence: float):
        """Log conversation exchange with context"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'ai_response_preview': ai_response[:100] + '...' if len(ai_response) > 100 else ai_response,
            'intent': intent,
            'confidence': confidence,
            'input_length': len(user_input),
            'response_length': len(ai_response)
        }
        
        self.logger.info("Conversation exchange", extra=log_data)
    
    def log_context_confusion(self, user_input: str, expected_action: str, actual_response: str):
        """Log when context confusion occurs"""
        self.logger.warning(
            "Context confusion detected",
            extra={
                'user_input': user_input,
                'expected_action': expected_action,
                'actual_response_preview': actual_response[:100],
                'issue': 'affirmative_misinterpreted'
            }
        )


# Singleton instance
_conversation_logger: ConversationLogger = None


def get_conversation_logger() -> ConversationLogger:
    """Get or create conversation logger instance"""
    global _conversation_logger
    if _conversation_logger is None:
        _conversation_logger = ConversationLogger()
    return _conversation_logger

