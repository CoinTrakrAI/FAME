"""Voice session models for FAME's enterprise voice pipeline."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class SessionMetrics:
    """Operational metrics collected per voice session."""

    utterances_processed: int = 0
    recogniser_failures: int = 0
    output_failures: int = 0
    average_latency_ms: float = 0.0
    max_latency_ms: float = 0.0

    def record_latency(self, latency_ms: float) -> None:
        self.utterances_processed += 1
        if self.utterances_processed == 1:
            self.average_latency_ms = latency_ms
            self.max_latency_ms = latency_ms
            return

        total_latency = self.average_latency_ms * (self.utterances_processed - 1) + latency_ms
        self.average_latency_ms = total_latency / self.utterances_processed
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)


@dataclass
class VoiceSession:
    """Represents an active voice session for a given user/device."""

    session_id: str
    channel_id: str
    created_at: float = field(default_factory=time.time)
    config_snapshot: Dict[str, str] = field(default_factory=dict)
    metrics: SessionMetrics = field(default_factory=SessionMetrics)
    locale: str = "en-US"
    last_activity_at: float = field(default_factory=time.time)
    is_active: bool = True
    context_user_name: Optional[str] = None

    def touch(self) -> None:
        """Update the last activity timestamp."""

        self.last_activity_at = time.time()

    def close(self) -> None:
        """Mark the session inactive."""

        self.is_active = False


