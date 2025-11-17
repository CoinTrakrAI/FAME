"""Fallback and clarification responses."""

from __future__ import annotations
import asyncio
import logging

from ..session_context import SessionContext
from ..types import IntentResult, ResponsePayload

logger = logging.getLogger(__name__)


def handle_low_confidence(user_text: str, context: SessionContext, intent: IntentResult) -> ResponsePayload:
    """
    Use autonomous response engine for low-confidence queries.
    FAME will use web scraping, Google AI, and stored knowledge to answer.
    """
    context.entities.pop("awaiting_code_details", None)
    
    # Try autonomous response engine first
    try:
        from core.autonomous_response_engine import get_autonomous_engine
        
        engine = get_autonomous_engine()
        
        # Prepare context for autonomous engine
        context_list = []
        for msg in context.history[-5:]:  # Last 5 messages
            role = "user" if msg.get("role") == "user" else "assistant"
            content = msg.get("content", "")
            if content:
                context_list.append({"role": role, "content": content})
        
        # Generate autonomous response
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            autonomous_response = loop.run_until_complete(
                engine.generate_response(user_text, context_list)
            )
            
            if autonomous_response and len(autonomous_response) > 20:
                # Successfully got autonomous response
                return ResponsePayload(
                    reply=autonomous_response,
                    intent="autonomous_response",
                    confidence=0.7,  # Moderate confidence for autonomous responses
                    trace={
                        "handler": "autonomous_engine",
                        "reason": "low_confidence_fallback",
                        "raw_intent": intent.intent,
                        "raw_confidence": intent.confidence,
                        "source": "web_scraping_or_ai"
                    },
                )
        finally:
            loop.close()
    except Exception as e:
        logger.debug(f"Autonomous engine error: {e}")
    
    # Fallback to clarification request
    message = (
        "I want to make sure I get that right. Could you share a bit more detail or "
        "try rephrasing your request?"
    )
    return ResponsePayload(
        reply=message,
        intent="clarification",
        confidence=intent.confidence,
        follow_up="Provide more details so I can help.",
        trace={
            "handler": "fallback",
            "reason": "low_confidence",
            "raw_intent": intent.intent,
            "raw_confidence": intent.confidence,
        },
    )


