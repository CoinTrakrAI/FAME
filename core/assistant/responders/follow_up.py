"""Handlers for short follow-up acknowledgements."""

from __future__ import annotations

from ..session_context import SessionContext
from ..types import IntentResult, ResponsePayload


def handle_positive(context: SessionContext, intent: IntentResult) -> ResponsePayload:
    if context.entities.get("awaiting_code_details"):
        message = "Great! Share any details about the program and I’ll walk you through the next steps."
    else:
        message = "Great! How can I assist you further?"

    return ResponsePayload(
        reply=message,
        intent="follow_up_positive",
        confidence=intent.confidence,
        trace={"handler": "follow_up_positive"},
    )


def handle_negative(context: SessionContext, intent: IntentResult) -> ResponsePayload:
    context.entities.pop("awaiting_code_details", None)
    message = "No problem. Let me know if there’s something else you’d like to explore."
    return ResponsePayload(
        reply=message,
        intent="follow_up_negative",
        confidence=intent.confidence,
        trace={"handler": "follow_up_negative"},
    )


