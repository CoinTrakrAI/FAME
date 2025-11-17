import asyncio

from orchestrator.strategy_engine import StrategyEngine


def test_strategy_engine_generates_portfolio():
    engine = StrategyEngine()
    raw = {
        "returns": [0.01] * 40,
        "momentum": {"AAPL": 0.4},
        "zscores": {"AAPL": 2.2},
        "spreads": {"AAPL": 0.001},
        "liquidity": {"AAPL": 1000},
        "order_book": {"bid_volume": 120, "ask_volume": 80, "depth": 60},
        "trades": {"buy_volume": 90, "sell_volume": 70},
        "cross_asset_correlations": {"AAPL": 0.3},
    }
    intelligence = {
        "regime_shift_intelligence": {"current_regime": {"type": "trending_bull"}},
        "unified_signals": {"meta": {"confidence": 0.8}},
        "risk_intelligence": {
            "metrics": {
                "var_95": -0.02,
                "cvar_99": -0.03,
                "max_drawdown": -0.05,
                "volatility": 0.03,
                "sharpe_ratio": 1.1,
            }
        },
    }
    portfolio = asyncio.run(engine.generate_portfolio(raw, intelligence=intelligence))
    positions = portfolio["positions"]
    assert positions
    for size in positions.values():
        assert abs(size) <= engine.risk_orchestrator.constraints.max_position + 1e-9
    assert portfolio["metadata"]["regime"] == "trending_bull"
    assert portfolio["metadata"]["strategy_weights"]
    assert portfolio["metadata"]["allocation_weights"]

