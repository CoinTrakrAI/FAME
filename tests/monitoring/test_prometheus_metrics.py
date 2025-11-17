
import asyncio
import time

import pytest

try:
    from prometheus_client import CollectorRegistry
except ImportError:  # pragma: no cover
    CollectorRegistry = None  # type: ignore

from monitoring.prometheus_metrics import AdvancedRiskMetrics, MonitoringIntegration, TradingMetrics


def test_trading_metrics_instantiation():
    registry = CollectorRegistry() if CollectorRegistry else None
    metrics = TradingMetrics(port=0, registry=registry)
    metrics.update_training_metrics({})
    metrics.update_strategy_metrics({})
    metrics.update_risk_metrics({})
    metrics.update_market_metrics({})
    metrics.record_inference_latency("test", start_time=time.time())


def test_advanced_risk_metrics_handles_empty_portfolio():
    registry = CollectorRegistry() if CollectorRegistry else None
    metrics = TradingMetrics(port=0, registry=registry)
    risk_metrics = AdvancedRiskMetrics(metrics)
    result = risk_metrics.calculate_advanced_risk_metrics({}, {})
    assert "var_95" in result


def test_monitoring_integration_instruments_components():
    class DummyTraining:
        async def _advanced_training_cycle(self):
            return {"multi_agent": {"agent": {"reward": 0.5}}}

    class DummyRisk:
        def __init__(self):
            self.optimize_called = False

        def optimize_portfolio(self, *args, **kwargs):
            self.optimize_called = True
            return {"returns": [0.01, -0.02], "leverage": 1.5}

    class DummyStrategy:
        async def generate_portfolio(self, *args, **kwargs):
            return {"allocations": {"strat": {"weight": 0.5, "asset_class": "multi"}}}

    registry = CollectorRegistry() if CollectorRegistry else None
    config = {"metrics_port": 0}
    integration = MonitoringIntegration(config)

    async def run_checks():
        training = DummyTraining()
        await integration.instrument_training_system(training)
        await training._advanced_training_cycle()

        risk = DummyRisk()
        await integration.instrument_risk_system(risk)
        risk.optimize_portfolio({}, None, None)
        assert risk.optimize_called

        strategy = DummyStrategy()
        await integration.instrument_strategy_engine(strategy)
        await strategy.generate_portfolio({})

    asyncio.run(run_checks())

