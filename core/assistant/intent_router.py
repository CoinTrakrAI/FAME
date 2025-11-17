"""
Hybrid intent routing that combines pattern recognition, context memory,
and the legacy NLU stack to improve conversational accuracy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from .types import IntentResult
from .session_context import SessionContext

try:
    from .nlu import parse_intent as legacy_parse_intent
except ImportError:  # pragma: no cover - legacy modules may be optional
    legacy_parse_intent = None


_GREETING_PATTERN = re.compile(
    r"^(?:hi|hello|hey|heya|hiya|good\s+(?:morning|afternoon|evening)|greetings|yo|sup)[!?.,\s]*$",
    re.IGNORECASE,
)

_CODE_HELP_PATTERNS = [
    re.compile(pat, re.IGNORECASE)
    for pat in (
        r"\bhelp\s+me\s+(?:write|code|create|build)\b",
        r"\bcan\s+you\s+(?:help|assist)\s+(?:me\s+)?(?:write|build|code)\b",
        r"\bwrite\s+(?:a|the)?\s*(?:program|script|app|application)\b",
        r"\b(?:can\s+you\s+)?build\s+(?:an?|the)?\s*(?:api|program|tool|solution|application|app)\b",
        r"\bmake\s+(?:me\s+)?(?:a|the)?\s*(?:bot|program|script)\b",
        r"\bcreate\s+(?:an?|the)?\s*(?:application|app|program|software)\b",
        r"\bdevelop\s+(?:an?|the)?\s*(?:program|application|tool)\b",
    )
]

_AFFIRMATIVE_RESPONSES = {"yes", "yeah", "yep", "sure", "absolutely", "please do", "do it", "go ahead"}
_NEGATIVE_RESPONSES = {"no", "nope", "nah", "stop", "cancel", "never mind", "nevermind"}


class IntentRouter:
    """
    Lightweight orchestrator that enriches the legacy NLU with pattern checks
    and conversation context before returning a normalized IntentResult.
    """

    def __init__(self, low_confidence_floor: float = 0.15) -> None:
        self._low_confidence_floor = low_confidence_floor

    def route(self, user_text: str, context: SessionContext) -> IntentResult:
        text = (user_text or "").strip()
        lowered = text.lower()

        if not text:
            return IntentResult(intent="unknown", confidence=0.0, rationale="empty_input")

        # Strong greeting detection to avoid unnecessary web lookups.
        if _GREETING_PATTERN.match(text):
            return IntentResult(intent="greet", confidence=0.95, rationale="greeting_pattern")

        # Detect quick affirmations/negations to support follow-ups.
        if lowered in _AFFIRMATIVE_RESPONSES and context.last_intent:
            return IntentResult(intent="follow_up_positive", confidence=0.6, rationale="affirmation_followup")

        if lowered in _NEGATIVE_RESPONSES and context.last_intent:
            return IntentResult(intent="follow_up_negative", confidence=0.6, rationale="negation_followup")

        # Specialist logic for coding help questions – prevents generic web search answers.
        for pattern in _CODE_HELP_PATTERNS:
            if pattern.search(text):
                return IntentResult(intent="code_help", confidence=0.8, rationale=f"code_help:{pattern.pattern}")

        # Fall back to the legacy parser for the broader taxonomy.
        legacy_result: Dict[str, any] = (
            legacy_parse_intent(text) if callable(legacy_parse_intent) else {"intent": "unknown", "confidence": 0.0}
        )

        intent = legacy_result.get("intent", "unknown")
        confidence = float(legacy_result.get("confidence", 0.0) or 0.0)
        slots = legacy_result.get("slots", {}) or {}

        # If the legacy parser returned a greeting with weak confidence, boost it.
        if intent == "greet" and confidence < 0.75:
            confidence = 0.9

        # Normalize very low values to a deterministic baseline.
        if confidence < self._low_confidence_floor:
            confidence = self._low_confidence_floor

        return IntentResult(
            intent=intent,
            confidence=confidence,
            slots=slots,
            rationale=legacy_result.get("rationale", "legacy_nlu"),
        )


