"""
Shared data structures for the FAME assistant conversation pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class IntentResult:
    """Normalized representation of classifier output."""

    intent: str
    confidence: float
    slots: Dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    entities: Dict[str, Any] = field(default_factory=dict)

    def combined_slots(self) -> Dict[str, Any]:
        """Return a merged view of structured data."""
        combined = dict(self.slots)
        if self.entities:
            combined.update(self.entities)
        return combined


@dataclass
class ResponsePayload:
    """Canonical response envelope used by high-level orchestrator."""

    reply: str
    intent: str
    confidence: float
    trace: Dict[str, Any] = field(default_factory=dict)
    follow_up: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: bool = False


