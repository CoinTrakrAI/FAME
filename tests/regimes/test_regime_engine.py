import asyncio

from regimes.regime_engine import RegimeDetectionEngine
from regimes.regime_types import MarketRegime


def test_regime_detection_engine_basic():
    engine = RegimeDetectionEngine()
    market_data = {
        "returns": [0.01] * 30,
        "macro": {"growth": 1.0, "inflation": 0.1},
        "cross_asset_correlations": {"asset_a": 0.5, "asset_b": 0.6},
    }
    regime = asyncio.run(engine.analyze(market_data))
    assert isinstance(regime, MarketRegime)

