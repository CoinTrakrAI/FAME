"""Production tests for the trading telemetry exporter."""

from __future__ import annotations

import threading
import time
import unittest
import urllib.request
from unittest.mock import Mock

from monitoring.trading_metrics_exporter import TradingMetrics, create_trading_exporter


class TradingTelemetryExporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = Mock(
            return_value={
                "metrics": {
                    "api_calls": 100,
                    "api_errors": 2,
                    "circuit_breaker_trips": 1,
                    "signals_generated": 50,
                    "last_signal_latency_ms": 150.0,
                    "portfolio_value": 100_000.0,
                    "active_strategies": 3,
                    "executed_trades": 10,
                    "buy_orders": 6,
                    "sell_orders": 4,
                    "win_trades": 7,
                    "loss_trades": 3,
                    "projected_roi_avg": 0.12,
                    "orders_submitted": 3,
                    "orders_filled": 3,
                    "orders_rejected": 0,
                    "execution_notional": 12_500.0,
                    "execution_slippage_bps_avg": 3.2,
                    "execution_latency_ms_avg": 120.0,
                    "execution_latency_ms_last": 110.0,
                },
                "health": {
                    "status": "healthy",
                    "finnhub": "healthy",
                    "strategies": "healthy",
                },
            }
        )
        self.exporter = create_trading_exporter(self.provider)

    def tearDown(self) -> None:
        self.exporter.stop_http_server()

    def test_prometheus_output_contains_metrics(self) -> None:
        metrics = TradingMetrics(
            api_calls=100,
            api_errors=3,
            circuit_breaker_trips=2,
            signals_generated=60,
            last_signal_latency_ms=200.0,
            portfolio_value=120_000.0,
            active_strategies=4,
            health_status=1,
            executed_trades=12,
            buy_orders=7,
            sell_orders=5,
            win_trades=8,
            loss_trades=4,
            projected_roi_avg=0.15,
            orders_submitted=4,
            orders_filled=4,
            orders_rejected=0,
            execution_notional=25_000.0,
            execution_slippage_bps_avg=2.5,
            execution_latency_ms_avg=95.0,
            execution_latency_ms_last=90.0,
        )
        self.exporter.update_metrics(metrics)
        prom = self.exporter.as_prometheus()
        self.assertIn("trading_api_calls_total", prom)
        self.assertIn("trading_health_status", prom)
        self.assertIn("trading_projected_roi_avg", prom)

    def test_dict_output_fallback_on_error(self) -> None:
        faulty_exporter = create_trading_exporter(Mock(side_effect=Exception("boom")))
        result = faulty_exporter.as_dict()
        self.assertEqual(result["trading_health_status"], 0.0)

    def test_http_server_endpoints(self) -> None:
        self.exporter.start_http_server(host="127.0.0.1", port=0)
        time.sleep(0.1)
        server = self.exporter._http_server
        self.assertIsNotNone(server)
        host, port = server.server_address

        with urllib.request.urlopen(f"http://{host}:{port}/") as resp:
            payload = resp.read().decode("utf-8")
            self.assertIn("FAME Trading Telemetry", payload)

        with urllib.request.urlopen(f"http://{host}:{port}/health") as resp:
            payload = resp.read().decode("utf-8")
            self.assertIn("status", payload)

        with urllib.request.urlopen(f"http://{host}:{port}/metrics") as resp:
            payload = resp.read().decode("utf-8")
            self.assertIn("trading_api_calls_total", payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)


