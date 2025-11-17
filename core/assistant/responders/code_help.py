"""Clarification-focused handler for programming assistance requests."""

from __future__ import annotations

import re
from typing import Optional

from ..session_context import SessionContext
from ..types import IntentResult, ResponsePayload

_LANGUAGE_HINTS = {
    "python": "Python",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "java": "Java",
    "c#": "C#",
    "c++": "C++",
    "rust": "Rust",
    "go": "Go",
    "golang": "Go",
    "swift": "Swift",
}


def _extract_language(user_text: str) -> Optional[str]:
    lowered = user_text.lower()
    for key, display in _LANGUAGE_HINTS.items():
        if re.search(rf"\b{re.escape(key)}\b", lowered):
            return display
    return None


def handle(user_text: str, context: SessionContext, intent: IntentResult) -> ResponsePayload:
    """
    Ask guiding questions so FAME can provide targeted code assistance rather than
    returning generic snippets pulled from external search.
    """
    detected_language = _extract_language(user_text)
    context.entities["awaiting_code_details"] = True
    if detected_language:
        context.entities["preferred_language"] = detected_language

    if detected_language:
        message = (
            f"I can definitely help you code in {detected_language}. "
            "Could you share a quick summary of what the program should do?"
        )
    else:
        message = (
            "I'd be happy to help you write a program. "
            "What language would you like to use, and what should the program accomplish?"
        )

    return ResponsePayload(
        reply=message,
        intent=intent.intent,
        confidence=max(intent.confidence, 0.85),
        follow_up="Describe the program's goal and preferred language.",
        trace={
            "handler": "code_help",
            "detected_language": detected_language,
        },
        metadata={"awaiting_details": True},
    )


