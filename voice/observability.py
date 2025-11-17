"""Observability utilities for the voice pipeline."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Dict


logger = logging.getLogger(__name__)


@dataclass
class VoiceMetrics:
    total_requests: int = 0
    failed_requests: int = 0
    average_latency_ms: float = 0.0
    last_updated: float = field(default_factory=time.time)
    wake_events: int = 0
    wake_false_positives: int = 0

    def record_request(self, latency_ms: float, success: bool) -> None:
        self.total_requests += 1
        if not success:
            self.failed_requests += 1
        if self.total_requests == 1:
            self.average_latency_ms = latency_ms
        else:
            aggregate = self.average_latency_ms * (self.total_requests - 1) + latency_ms
            self.average_latency_ms = aggregate / self.total_requests
        self.last_updated = time.time()

    def record_wake(self, false_positive: bool = False) -> None:
        if not false_positive:
            self.wake_events += 1
        else:
            self.wake_false_positives += 1
        self.last_updated = time.time()


class VoiceTelemetry:
    """Thread-safe metrics registry for voice operations."""

    def __init__(self) -> None:
        self._metrics = VoiceMetrics()
        self._lock = threading.Lock()

    def record(self, latency_ms: float, success: bool) -> None:
        with self._lock:
            self._metrics.record_request(latency_ms, success)

    def record_wake_event(self, false_positive: bool = False) -> None:
        with self._lock:
            self._metrics.record_wake(false_positive=false_positive)

    def snapshot(self) -> Dict[str, float]:
        with self._lock:
            metrics_copy = VoiceMetrics(
                total_requests=self._metrics.total_requests,
                failed_requests=self._metrics.failed_requests,
                average_latency_ms=self._metrics.average_latency_ms,
                last_updated=self._metrics.last_updated,
                wake_events=self._metrics.wake_events,
                wake_false_positives=self._metrics.wake_false_positives,
            )
        return {
            "voice_total_requests": float(metrics_copy.total_requests),
            "voice_failed_requests": float(metrics_copy.failed_requests),
            "voice_average_latency_ms": metrics_copy.average_latency_ms,
            "voice_metrics_last_updated": metrics_copy.last_updated,
            "voice_wake_events": float(metrics_copy.wake_events),
            "voice_wake_false_positives": float(metrics_copy.wake_false_positives),
        }

    def prometheus_metrics(self) -> str:
        snapshot = self.snapshot()
        lines = []
        for key, value in snapshot.items():
            metric_name = key.replace(".", "_")
            lines.append(f"{metric_name} {value}")
        return "\n".join(lines) + "\n"


