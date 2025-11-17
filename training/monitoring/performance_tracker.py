"""
Training performance monitoring with Prometheus integration.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional

try:
    from prometheus_client import Gauge, Histogram, Summary
except ImportError:  # pragma: no cover - optional dependency
    Gauge = Histogram = Summary = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PerformanceSnapshot:
    timestamp: datetime
    policy_version: str
    reward_avg: float
    rolling_roi: Optional[float] = None
    win_rate: Optional[float] = None
    regret: Optional[float] = None
    latency_ms: Optional[float] = None
    experience_count: int = 0
    experience_buffer_size: int = 0
    drift_score: Optional[float] = None

    def as_dict(self) -> Dict[str, object]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "policy_version": self.policy_version,
            "reward_avg": self.reward_avg,
            "rolling_roi": self.rolling_roi,
            "win_rate": self.win_rate,
            "regret": self.regret,
            "latency_ms": self.latency_ms,
            "experience_count": self.experience_count,
            "experience_buffer_size": self.experience_buffer_size,
            "drift_score": self.drift_score,
        }


class TrainingPerformanceTracker:
    """
    Aggregates live performance metrics and exposes them to Prometheus.
    """

    def __init__(self, registry=None, history_limit: int = 100) -> None:
        self.history: Deque[PerformanceSnapshot] = deque(maxlen=history_limit)
        self.registry = registry

        self.reward_gauge = _safe_gauge(
            "training_policy_reward_avg",
            "Average reward for latest training cycle",
            ["policy_version"],
            registry=registry,
        )
        self.win_rate_gauge = _safe_gauge(
            "training_policy_win_rate",
            "Rolling win rate for policy decisions",
            ["policy_version"],
            registry=registry,
        )
        self.roi_gauge = _safe_gauge(
            "training_policy_rolling_roi",
            "Rolling ROI achieved by the current policy",
            ["policy_version"],
            registry=registry,
        )
        self.regret_gauge = _safe_gauge(
            "training_policy_regret",
            "Estimated regret of current policy vs benchmark",
            ["policy_version"],
            registry=registry,
        )
        self.latency_hist = _safe_histogram(
            "training_policy_latency_ms",
            "End-to-end latency for intelligence to policy update",
            registry=registry,
        )
        self.buffer_gauge = _safe_gauge(
            "training_experience_buffer_size",
            "Current number of experiences stored in buffer",
            registry=registry,
        )
        self.drift_summary = _safe_summary(
            "training_policy_drift_score",
            "Distribution of policy drift detection scores",
            registry=registry,
        )

    def record_snapshot(self, snapshot: PerformanceSnapshot) -> None:
        self.history.append(snapshot)

        if self.reward_gauge:
            self.reward_gauge.labels(policy_version=snapshot.policy_version).set(snapshot.reward_avg)
        if self.win_rate_gauge and snapshot.win_rate is not None:
            self.win_rate_gauge.labels(policy_version=snapshot.policy_version).set(snapshot.win_rate)
        if self.roi_gauge and snapshot.rolling_roi is not None:
            self.roi_gauge.labels(policy_version=snapshot.policy_version).set(snapshot.rolling_roi)
        if self.regret_gauge and snapshot.regret is not None:
            self.regret_gauge.labels(policy_version=snapshot.policy_version).set(snapshot.regret)
        if self.latency_hist and snapshot.latency_ms is not None:
            self.latency_hist.observe(snapshot.latency_ms)
        if self.buffer_gauge:
            self.buffer_gauge.set(snapshot.experience_buffer_size)
        if self.drift_summary and snapshot.drift_score is not None:
            self.drift_summary.observe(snapshot.drift_score)

        logger.debug(
            "Training snapshot recorded",
            extra={"policy_version": snapshot.policy_version, "reward": snapshot.reward_avg},
        )

    def recent_snapshots(self, limit: int = 20) -> List[Dict[str, object]]:
        return [snap.as_dict() for snap in list(self.history)[-limit:]]


def _safe_gauge(name: str, documentation: str, labelnames: Optional[List[str]] = None, registry=None):
    if Gauge is None:
        return None
    return Gauge(name, documentation, labelnames=labelnames or [], registry=registry)


def _safe_histogram(name: str, documentation: str, registry=None):
    if Histogram is None:
        return None
    return Histogram(name, documentation, registry=registry)


def _safe_summary(name: str, documentation: str, registry=None):
    if Summary is None:
        return None
    return Summary(name, documentation, registry=registry)

