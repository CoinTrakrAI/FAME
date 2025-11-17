"""Production-grade trading telemetry exporter with Prometheus support."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest


logger = logging.getLogger(__name__)


@dataclass
class TradingMetrics:
    api_calls: int = 0
    api_errors: int = 0
    circuit_breaker_trips: int = 0
    signals_generated: int = 0
    last_signal_latency_ms: float = 0.0
    portfolio_value: float = 0.0
    active_strategies: int = 0
    health_status: int = 1
    executed_trades: int = 0
    buy_orders: int = 0
    sell_orders: int = 0
    win_trades: int = 0
    loss_trades: int = 0
    projected_roi_avg: float = 0.0
    orders_submitted: int = 0
    orders_filled: int = 0
    orders_rejected: int = 0
    execution_notional: float = 0.0
    execution_slippage_bps_avg: float = 0.0
    execution_latency_ms_avg: float = 0.0
    execution_latency_ms_last: float = 0.0


class TradingTelemetryExporter:
    def __init__(self, provider: Callable[[], Dict[str, Any]]) -> None:
        self._provider = provider
        self._http_server: Optional[HTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None
        self._start_time = time.time()
        self._registry = CollectorRegistry()
        self._previous_counters = {
            "api_calls": 0,
            "api_errors": 0,
            "circuit_breaker_trips": 0,
            "signals_generated": 0,
            "win_trades": 0,
            "loss_trades": 0,
        }
        self._init_prometheus_metrics()
        logger.info("TradingTelemetryExporter initialised")

    def _init_prometheus_metrics(self) -> None:
        self.api_calls_counter = Counter(
            "trading_api_calls_total",
            "Total trading API calls",
            ["provider"],
            registry=self._registry,
        )
        self.api_errors_counter = Counter(
            "trading_api_errors_total",
            "Total trading API errors",
            ["provider", "error_type"],
            registry=self._registry,
        )
        self.circuit_breaker_trips_counter = Counter(
            "trading_circuit_breaker_trips_total",
            "Circuit breaker activations",
            registry=self._registry,
        )
        self.signals_generated_counter = Counter(
            "trading_signals_generated_total",
            "Trading signals generated",
            ["strategy"],
            registry=self._registry,
        )
        self.win_trades_counter = Counter(
            "trading_win_trades_total",
            "Trades classified as wins",
            registry=self._registry,
        )
        self.loss_trades_counter = Counter(
            "trading_loss_trades_total",
            "Trades classified as losses",
            registry=self._registry,
        )

        self.last_signal_latency_gauge = Gauge(
            "trading_last_signal_latency_seconds",
            "Latency of the last generated signal",
            registry=self._registry,
        )
        self.portfolio_value_gauge = Gauge(
            "trading_portfolio_value",
            "Reported portfolio value",
            registry=self._registry,
        )
        self.active_strategies_gauge = Gauge(
            "trading_active_strategies",
            "Active trading strategies",
            registry=self._registry,
        )
        self.health_status_gauge = Gauge(
            "trading_health_status",
            "Trading health status (1 healthy, 0 unhealthy)",
            registry=self._registry,
        )
        self.executed_trades_gauge = Gauge(
            "trading_executed_trades",
            "Total executed trades",
            registry=self._registry,
        )
        self.buy_orders_gauge = Gauge(
            "trading_buy_orders",
            "Total buy orders handled",
            registry=self._registry,
        )
        self.sell_orders_gauge = Gauge(
            "trading_sell_orders",
            "Total sell orders handled",
            registry=self._registry,
        )
        self.projected_roi_avg_gauge = Gauge(
            "trading_projected_roi_avg",
            "Average projected ROI",
            registry=self._registry,
        )
        self.execution_orders_submitted_gauge = Gauge(
            "trading_execution_orders_submitted",
            "Execution orders submitted total",
            registry=self._registry,
        )
        self.execution_orders_filled_gauge = Gauge(
            "trading_execution_orders_filled",
            "Execution orders filled total",
            registry=self._registry,
        )
        self.execution_orders_rejected_gauge = Gauge(
            "trading_execution_orders_rejected",
            "Execution orders rejected total",
            registry=self._registry,
        )
        self.execution_notional_gauge = Gauge(
            "trading_execution_notional",
            "Total notional traded during execution",
            registry=self._registry,
        )
        self.execution_slippage_bps_gauge = Gauge(
            "trading_execution_slippage_bps_avg",
            "Average execution slippage in basis points",
            registry=self._registry,
        )
        self.execution_latency_avg_gauge = Gauge(
            "trading_execution_latency_ms_avg",
            "Average execution latency in milliseconds",
            registry=self._registry,
        )
        self.execution_latency_last_gauge = Gauge(
            "trading_execution_latency_ms_last",
            "Latency of the last execution in milliseconds",
            registry=self._registry,
        )

        self.signal_latency_histogram = Histogram(
            "trading_signal_latency_seconds",
            "Distribution of signal generation latency",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self._registry,
        )

    def _update_counters(self, metrics: TradingMetrics) -> None:
        deltas = {
            "api_calls": metrics.api_calls - self._previous_counters["api_calls"],
            "api_errors": metrics.api_errors - self._previous_counters["api_errors"],
            "circuit_breaker_trips": metrics.circuit_breaker_trips
            - self._previous_counters["circuit_breaker_trips"],
            "signals_generated": metrics.signals_generated
            - self._previous_counters["signals_generated"],
            "win_trades": metrics.win_trades - self._previous_counters["win_trades"],
            "loss_trades": metrics.loss_trades - self._previous_counters["loss_trades"],
        }

        if deltas["api_calls"] > 0:
            self.api_calls_counter.labels(provider="aggregate").inc(deltas["api_calls"])
            self._previous_counters["api_calls"] = metrics.api_calls
        if deltas["api_errors"] > 0:
            self.api_errors_counter.labels(provider="aggregate", error_type="aggregate").inc(
                deltas["api_errors"]
            )
            self._previous_counters["api_errors"] = metrics.api_errors
        if deltas["circuit_breaker_trips"] > 0:
            self.circuit_breaker_trips_counter.inc(deltas["circuit_breaker_trips"])
            self._previous_counters["circuit_breaker_trips"] = metrics.circuit_breaker_trips
        if deltas["signals_generated"] > 0:
            self.signals_generated_counter.labels(strategy="aggregate").inc(
                deltas["signals_generated"]
            )
            self._previous_counters["signals_generated"] = metrics.signals_generated
        if deltas["win_trades"] > 0:
            self.win_trades_counter.inc(deltas["win_trades"])
            self._previous_counters["win_trades"] = metrics.win_trades
        if deltas["loss_trades"] > 0:
            self.loss_trades_counter.inc(deltas["loss_trades"])
            self._previous_counters["loss_trades"] = metrics.loss_trades

    def update_metrics(self, metrics: TradingMetrics) -> None:
        try:
            self._update_counters(metrics)
            latency_seconds = max(0.0, metrics.last_signal_latency_ms / 1000.0)
            self.last_signal_latency_gauge.set(latency_seconds)
            if latency_seconds > 0:
                self.signal_latency_histogram.observe(latency_seconds)
            self.portfolio_value_gauge.set(metrics.portfolio_value)
            self.active_strategies_gauge.set(metrics.active_strategies)
            self.health_status_gauge.set(metrics.health_status)
            self.executed_trades_gauge.set(metrics.executed_trades)
            self.buy_orders_gauge.set(metrics.buy_orders)
            self.sell_orders_gauge.set(metrics.sell_orders)
            self.projected_roi_avg_gauge.set(metrics.projected_roi_avg)
            self.execution_orders_submitted_gauge.set(metrics.orders_submitted)
            self.execution_orders_filled_gauge.set(metrics.orders_filled)
            self.execution_orders_rejected_gauge.set(metrics.orders_rejected)
            self.execution_notional_gauge.set(metrics.execution_notional)
            self.execution_slippage_bps_gauge.set(metrics.execution_slippage_bps_avg)
            self.execution_latency_avg_gauge.set(metrics.execution_latency_ms_avg)
            self.execution_latency_last_gauge.set(metrics.execution_latency_ms_last)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to update trading metrics: %s", exc)

    def as_dict(self) -> Dict[str, float]:
        try:
            telemetry = self._provider()
            metrics_data = telemetry.get("metrics", {})
            health_data = telemetry.get("health", {})
            trading_metrics = TradingMetrics(
                api_calls=metrics_data.get("api_calls", 0),
                api_errors=metrics_data.get("api_errors", 0),
                circuit_breaker_trips=metrics_data.get("circuit_breaker_trips", 0),
                signals_generated=metrics_data.get("signals_generated", 0),
                last_signal_latency_ms=metrics_data.get("last_signal_latency_ms", 0.0),
                portfolio_value=metrics_data.get("portfolio_value", 0.0),
                active_strategies=metrics_data.get("active_strategies", 0),
                health_status=1 if health_data.get("status", "healthy") == "healthy" else 0,
                executed_trades=metrics_data.get("executed_trades", 0),
                buy_orders=metrics_data.get("buy_orders", 0),
                sell_orders=metrics_data.get("sell_orders", 0),
                win_trades=metrics_data.get("win_trades", 0),
                loss_trades=metrics_data.get("loss_trades", 0),
                projected_roi_avg=metrics_data.get("projected_roi_avg", 0.0),
                orders_submitted=metrics_data.get("orders_submitted", 0),
                orders_filled=metrics_data.get("orders_filled", 0),
                orders_rejected=metrics_data.get("orders_rejected", 0),
                execution_notional=metrics_data.get("execution_notional", 0.0),
                execution_slippage_bps_avg=metrics_data.get("execution_slippage_bps_avg", 0.0),
                execution_latency_ms_avg=metrics_data.get("execution_latency_ms_avg", 0.0),
                execution_latency_ms_last=metrics_data.get("execution_latency_ms_last", 0.0),
            )
            self.update_metrics(trading_metrics)
            merged: Dict[str, float] = {}
            for key, value in metrics_data.items():
                try:
                    merged[f"trading_{key}"] = float(value)
                except (TypeError, ValueError):
                    continue
            status_value = 1.0 if health_data.get("status", "healthy") == "healthy" else 0.0
            merged["trading_health_status"] = status_value
            return merged
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error collecting trading telemetry: %s", exc)
            return {"trading_health_status": 0.0}

    def as_prometheus(self) -> str:
        try:
            self.as_dict()
            return generate_latest(self._registry).decode("utf-8")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to render Prometheus metrics: %s", exc)
            return ""

    def as_health_check(self) -> Dict[str, Any]:
        try:
            telemetry = self._provider()
            health_data = telemetry.get("health", {})
            return {
                "status": health_data.get("status", "unknown"),
                "timestamp": time.time(),
                "uptime_seconds": time.time() - self._start_time,
                "components": {
                    "api_connectivity": health_data.get("finnhub", "unknown"),
                    "strategy_engine": health_data.get("strategies", "unknown"),
                    "data_feeds": health_data.get("data_feeds", "unknown"),
                },
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error generating trading health check: %s", exc)
            return {"status": "error", "error": str(exc)}

    def start_http_server(self, host: str = "0.0.0.0", port: int = 8775) -> None:
        if self._http_server:
            logger.info("Trading metrics HTTP server already running")
            return

        exporter = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                try:
                    if self.path == "/metrics":
                        payload = exporter.as_prometheus().encode("utf-8")
                        self._respond(200, payload, "text/plain; version=0.0.4")
                    elif self.path == "/health":
                        payload = json.dumps(exporter.as_health_check(), indent=2).encode("utf-8")
                        self._respond(200, payload, "application/json")
                    elif self.path == "/":
                        info = {
                            "service": "FAME Trading Telemetry",
                            "endpoints": {
                                "/metrics": "Prometheus metrics",
                                "/health": "Health status",
                                "/": "Service info",
                            },
                            "version": "1.0.0",
                        }
                        payload = json.dumps(info, indent=2).encode("utf-8")
                        self._respond(200, payload, "application/json")
                    else:
                        self.send_error(404, "Endpoint not found")
                except Exception as exc:  # pragma: no cover
                    logger.error("Trading telemetry HTTP handler error: %s", exc)
                    self.send_error(500, "internal server error")

            def _respond(self, status: int, payload: bytes, content_type: str) -> None:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(payload)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                logger.info("TradingTelemetry HTTP %s - %s", self.address_string(), format % args)

        self._http_server = HTTPServer((host, port), Handler)
        actual_host, actual_port = self._http_server.server_address
        self._http_thread = threading.Thread(
            target=self._http_server.serve_forever,
            name="TradingTelemetryHTTPServer",
            daemon=True,
        )
        self._http_thread.start()
        logger.info("Trading metrics HTTP server running on %s:%s", actual_host, actual_port)

    def stop_http_server(self) -> None:
        if self._http_server:
            logger.info("Stopping trading telemetry HTTP server")
            self._http_server.shutdown()
            self._http_server.server_close()
            self._http_server = None
        if self._http_thread:
            self._http_thread.join(timeout=5.0)
            if self._http_thread.is_alive():
                logger.warning("Trading telemetry HTTP thread did not stop gracefully")
            self._http_thread = None
        logger.info("Trading metrics HTTP server stopped")

    async def continuous_export(self, interval_seconds: int = 30) -> None:
        while True:
            try:
                self.as_dict()
            except Exception as exc:  # pragma: no cover
                logger.error("Continuous trading telemetry export failed: %s", exc)
            await asyncio.sleep(interval_seconds)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_http_server()


def create_trading_exporter(provider: Callable[[], Dict[str, Any]]) -> TradingTelemetryExporter:
    return TradingTelemetryExporter(provider)


__all__ = ["TradingTelemetryExporter", "TradingMetrics", "create_trading_exporter"]

