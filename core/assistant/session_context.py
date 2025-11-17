"""
Utility helpers for working with conversational session state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .dialog_manager import Session

_ASSISTANT_CTX_KEY = "_assistant_ctx"


@dataclass
class SessionContext:
    """Rich context wrapper for dialog_manager.Session."""

    session: Session
    session_id: str
    last_intent: Optional[str] = None
    last_confidence: float = 0.0
    entities: Dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0

    @property
    def metadata(self) -> Dict[str, Any]:
        """Expose underlying session metadata for convenience."""
        return self.session.user_metadata


def build_session_context(session: Session) -> SessionContext:
    """Create a SessionContext wrapper from a raw session object."""
    raw_ctx = session.user_metadata.get(_ASSISTANT_CTX_KEY, {})
    return SessionContext(
        session=session,
        session_id=session.id,
        last_intent=raw_ctx.get("last_intent"),
        last_confidence=raw_ctx.get("last_confidence", 0.0),
        entities=raw_ctx.get("entities", {}) or {},
        turn_count=raw_ctx.get("turn_count", 0),
    )


def persist_session_context(context: SessionContext) -> None:
    """Save the current SessionContext details back onto the session."""
    context.session.user_metadata[_ASSISTANT_CTX_KEY] = {
        "last_intent": context.last_intent,
        "last_confidence": context.last_confidence,
        "entities": context.entities,
        "turn_count": context.turn_count,
    }


