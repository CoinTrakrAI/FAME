import asyncio

from features.advanced_feature_engine import AdvancedFeatureEngine


def test_advanced_feature_engine_basic():
    engine = AdvancedFeatureEngine()
    raw = {
        "order_book": {"bid_volume": 100, "ask_volume": 80, "depth": 50},
        "trades": {"buy_volume": 120, "sell_volume": 90},
        "cross_asset_correlations": {"asset_a": 0.5, "asset_b": 0.3},
        "volatility_spillover": 0.2,
        "risk_premium_arbitrage": 0.1,
        "macro": {"growth": 2.0, "inflation": 0.5, "employment": 95},
        "sentiment": {"news": 0.1, "social": -0.2, "onchain": 0.3},
    }
    features = asyncio.run(engine.generate_features(raw))
    assert "order_book_imbalance" in features
    assert "avg_cross_asset_correlation" in features
    assert "macro_growth" in features
    assert "news_sentiment" in features

