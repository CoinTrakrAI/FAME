"""Production-grade trading tests without external dependencies."""

from __future__ import annotations

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, Mock, patch


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class TradingProductionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def test_technical_engine_fallback(self) -> None:
        from services import technical_indicators as ti

        ti._engine = None  # Reset singleton
        engine = ti.TechnicalAnalysisEngine()
        engine.mode = "pure_python"
        prices = [100, 101, 102, 101, 103, 105, 104, 106, 107, 108, 107, 106, 105, 104, 103]
        result = engine.calculate_rsi(prices)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.value, 0.0)
        self.assertLessEqual(result.value, 100.0)

    def test_decision_engine_financial_intent(self) -> None:
        from core.autonomous_decision_engine import AutonomousDecisionEngine

        engine = AutonomousDecisionEngine()
        intent, confidence, _ = self.loop.run_until_complete(engine.classify_intent("Get trading signals for AAPL"))
        self.assertEqual(intent, "financial")
        self.assertGreaterEqual(confidence, 0.6)

    def test_trading_service_handles_failure(self) -> None:
        from services.trading_service import TradingConfig, TradingService

        config = TradingConfig(finnhub_key="test", serpapi_key="", coingecko_key="", alpha_vantage_key="")
        service = TradingService(config)
        service.data_service.get_real_time_data = AsyncMock(return_value={})
        try:
            result = self.loop.run_until_complete(service.get_signals("FAIL"))
            self.assertIn("error", result)
        finally:
            self.loop.run_until_complete(service.shutdown())


class TradingSkillPluginTests(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def test_trading_skill_signal_flow(self) -> None:
        from services.trading_service import TradingConfig

        stub_service = AsyncMock()
        stub_service.get_signals.return_value = {
            "symbol": "AAPL",
            "signals": [
                {
                    "strategy": "momentum",
                    "signal_type": "BUY",
                    "confidence": 0.9,
                    "entry_price": 150.0,
                    "stop_loss": 145.0,
                    "take_profit": 160.0,
                }
            ],
        }
        stub_service.execute_trade.return_value = {"status": "success", "message": "Trade executed"}
        stub_service.record_projected_trade = Mock()

        with patch("config.trading_config.get_trading_config", return_value=TradingConfig("", "", "", "")), patch(
            "services.trading_service.get_trading_service", new=AsyncMock(return_value=stub_service)
        ), patch("skills.trading_skill.get_trading_service", new=AsyncMock(return_value=stub_service)), patch(
            "skills.trading_confirm.get_trading_service", new=AsyncMock(return_value=stub_service)
        ):
            from core import trading_skill_plugin

            trading_skill_plugin._trading_skill.trading_service = stub_service  # type: ignore

            result = self.loop.run_until_complete(
                trading_skill_plugin.handle({"text": "Get trading signal for AAPL", "session_id": "test"})
            )
            self.assertIn("response", result)
            self.assertIn("trading", result.get("source", ""))

            confirm_prompt = self.loop.run_until_complete(
                trading_skill_plugin.handle({"text": "buy AAPL", "session_id": "test"})
            )
            self.assertTrue(confirm_prompt.get("requires_confirmation"))

            confirm_result = self.loop.run_until_complete(
                trading_skill_plugin.handle({"text": "confirm", "session_id": "test"})
            )
            self.assertIn("response", confirm_result)
            stub_service.execute_trade.assert_awaited()
            stub_service.record_projected_trade.assert_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)


