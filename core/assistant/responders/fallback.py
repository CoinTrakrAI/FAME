"""Fallback and clarification responses."""

from __future__ import annotations

from ..session_context import SessionContext
from ..types import IntentResult, ResponsePayload


def handle_low_confidence(user_text: str, context: SessionContext, intent: IntentResult) -> ResponsePayload:
    """
    Encourage the user to clarify their request when intent confidence is
    insufficient for deterministic action.
    """
    context.entities.pop("awaiting_code_details", None)
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


