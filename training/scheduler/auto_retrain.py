"""
Auto-retraining scheduler based on performance snapshots and drift signals.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Optional

from training.monitoring import PerformanceSnapshot

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrainConfig:
    reward_drop_threshold: float = 0.15
    win_rate_threshold: float = 0.45
    drift_threshold: float = 0.4
    min_buffer_size: int = 500
    cooldown_minutes: int = 120


@dataclass(slots=True)
class RetrainDecision:
    trigger: bool
    reason: str
    timestamp: datetime


class AutoRetrainScheduler:
    """
    Evaluate training performance snapshots and trigger retraining when thresholds are violated.
    """

    def __init__(
        self,
        config: Optional[RetrainConfig] = None,
        callback: Optional[Callable[[RetrainDecision, PerformanceSnapshot], None]] = None,
    ) -> None:
        self.config = config or RetrainConfig()
        self.callback = callback
        self._last_trigger: Optional[datetime] = None

    def evaluate(self, snapshot: PerformanceSnapshot) -> Optional[RetrainDecision]:
        now = datetime.now(timezone.utc)
        if self._last_trigger and now - self._last_trigger < timedelta(minutes=self.config.cooldown_minutes):
            return None

        reasons = []
        if snapshot.reward_avg < self.config.reward_drop_threshold:
            reasons.append(f"reward_avg={snapshot.reward_avg:.3f}")
        if snapshot.win_rate is not None and snapshot.win_rate < self.config.win_rate_threshold:
            reasons.append(f"win_rate={snapshot.win_rate:.3f}")
        if snapshot.drift_score is not None and snapshot.drift_score > self.config.drift_threshold:
            reasons.append(f"drift_score={snapshot.drift_score:.3f}")
        if snapshot.experience_buffer_size < self.config.min_buffer_size:
            reasons.append(f"buffer_size={snapshot.experience_buffer_size}")

        if not reasons:
            return None

        decision = RetrainDecision(
            trigger=True,
            reason=", ".join(reasons),
            timestamp=now,
        )
        self._last_trigger = now
        logger.warning("Auto-retrain triggered: %s", decision.reason)
        if self.callback:
            try:
                self.callback(decision, snapshot)
            except Exception as exc:  # pragma: no cover
                logger.error("Auto-retrain callback failed: %s", exc)
        return decision

    def last_trigger_time(self) -> Optional[datetime]:
        return self._last_trigger

