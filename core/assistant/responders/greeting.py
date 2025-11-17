"""Warm, human-centric greeting handler."""

from __future__ import annotations

from typing import Optional

from ..session_context import SessionContext
from ..types import IntentResult, ResponsePayload


def handle(context: SessionContext, intent: IntentResult) -> ResponsePayload:
    """Craft a personalised greeting."""
    name: Optional[str] = context.metadata.get("name")
    if name:
        message = f"Hello {name}! How can I assist you today?"
    else:
        message = "Hello! I'm FAME. How can I help you today?"

    return ResponsePayload(
        reply=message,
        intent=intent.intent,
        confidence=max(intent.confidence, 0.9),
        trace={"handler": "greeting", "personalised": bool(name)},
    )


