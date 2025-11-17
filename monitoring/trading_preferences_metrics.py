"""Prometheus metrics helpers for trading preferences."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

PREFERENCE_UPDATE_COUNTER = Counter(
    "trading_preferences_updates_total",
    "Total trading preference updates",
    ["risk_level"],
)

PREFERENCE_ERROR_COUNTER = Counter(
    "trading_preferences_errors_total",
    "Trading preference errors by type",
    ["error_type"],
)

PREFERENCE_OPERATION_LATENCY = Histogram(
    "trading_preferences_operation_seconds",
    "Latency for preference operations",
)

PREFERENCE_CACHE_HIT_RATIO = Gauge(
    "trading_preferences_cache_hit_ratio",
    "Cache hit ratio for trading preferences",
)

__all__ = [
    "PREFERENCE_UPDATE_COUNTER",
    "PREFERENCE_ERROR_COUNTER",
    "PREFERENCE_OPERATION_LATENCY",
    "PREFERENCE_CACHE_HIT_RATIO",
]

