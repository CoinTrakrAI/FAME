"""Telemetry exporter for the trading service."""

from __future__ import annotations

from typing import Dict


class TradingTelemetryExporter:
    """Transforms trading metrics into the unified observability format."""

    def __init__(self, trading_service) -> None:
        self._service = trading_service
        self._prefix = "trading"

    async def export_metrics(self) -> Dict[str, float]:
        telemetry = self._service.telemetry()
        metrics = telemetry.get("metrics", {})
        health = telemetry.get("health", {})
        return {
            f"{self._prefix}.api_calls": float(metrics.get("api_calls", 0)),
            f"{self._prefix}.api_errors": float(metrics.get("api_errors", 0)),
            f"{self._prefix}.signals_generated": float(metrics.get("signals_generated", 0)),
            f"{self._prefix}.circuit_breaker_trips": float(metrics.get("circuit_breaker_trips", 0)),
            f"{self._prefix}.health_finnhub": 1.0 if health.get("finnhub") == "healthy" else 0.0,
            f"{self._prefix}.health_strategies": 1.0 if health.get("strategies") == "healthy" else 0.0,
        }

    async def health_check(self) -> Dict[str, str]:
        telemetry = self._service.telemetry()
        health = telemetry.get("health", {})
        status = "healthy" if all(val == "healthy" for val in health.values() if isinstance(val, str)) else "degraded"
        return {
            "service": "trading",
            "status": status,
            "details": str(health),
        }


__all__ = ["TradingTelemetryExporter"]


