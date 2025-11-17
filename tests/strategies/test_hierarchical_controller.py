import asyncio

from strategies.hierarchical_controller import HierarchicalStrategyController
from regimes.regime_types import MarketRegime


def test_hierarchical_controller_outputs_signals():
    controller = HierarchicalStrategyController()
    market_data = {
        "returns": [0.01] * 40,
        "momentum": {"AAPL": 0.5, "BTC": -0.3},
        "zscores": {"AAPL": 2.0, "ETH": -2.5},
        "spreads": {"AAPL": 0.001},
        "liquidity": {"AAPL": 1000.0},
        "macro": {"growth": 1.0, "inflation": 0.2, "employment": 95},
        "cross_asset_correlations": {"AAPL": 0.4, "BTC": 0.3},
        "order_book": {"bid_volume": 100, "ask_volume": 80, "depth": 50},
        "trades": {"buy_volume": 120, "sell_volume": 100},
    }
    regime, signals, weights = asyncio.run(controller.decide_action(market_data))
    assert signals
    assert isinstance(regime, MarketRegime)
    assert weights
    for signal in signals.values():
        assert -1.0 <= signal.direction <= 1.0
        assert 0.0 <= signal.confidence <= 1.0

