import asyncio

import numpy as np
import pytest
from intelligence.master_intelligence_engine import MasterIntelligenceEngine


@pytest.fixture
def engine() -> MasterIntelligenceEngine:
    return MasterIntelligenceEngine({"module_timeout": 5})


@pytest.fixture
def sample_market_data() -> dict:
    prices = {
        "BTCUSDT": [50000, 50100, 50200, 50350, 50420, 50500],
        "ETHUSDT": [3000, 3010, 3025, 3035, 3040, 3055],
    }
    returns = [0.01, -0.012, 0.008, -0.004, 0.006, -0.003]
    positions = {"BTCUSDT": 0.6, "ETHUSDT": 0.4}
    return {
        "prices": prices,
        "portfolio_returns": returns,
        "positions": positions,
        "portfolio_value": 250000,
        "leverage": 1.2,
        "timestamp": "2024-01-01T00:00:00Z",
    }


def test_generate_intelligence(engine: MasterIntelligenceEngine, sample_market_data: dict) -> None:
    bundle = asyncio.run(engine.generate_comprehensive_intelligence(sample_market_data))
    assert bundle.timestamp
    assert isinstance(bundle.correlation_intelligence, dict)
    assert isinstance(bundle.meta_confidence_scores, dict)
    assert "meta" in bundle.unified_signals
    assert bundle.risk_intelligence
    assert "metrics" in bundle.risk_intelligence


def test_parallel_execution(engine: MasterIntelligenceEngine, sample_market_data: dict) -> None:
    results = asyncio.run(engine._execute_modules_parallel(sample_market_data))
    assert results
    assert set(results.keys()).issuperset({"correlation", "volatility", "funding"})


def test_timeout_fallback(sample_market_data: dict) -> None:
    engine = MasterIntelligenceEngine({"module_timeout": 0.01})

    async def slow_analyze(_):
        await asyncio.sleep(0.05)
        return {"test": True}

    for module in engine.intelligence_modules.values():
        module.analyze = slow_analyze  # type: ignore[attr-defined]

    results = asyncio.run(engine._execute_modules_parallel(sample_market_data))
    assert all(result.get("error") == "timeout" for result in results.values())

