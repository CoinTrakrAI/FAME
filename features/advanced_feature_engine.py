"""Advanced feature engineering for trading."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(slots=True)
class MarketMicrostructureEngine:
    """Generate order book and trade flow features."""

    async def generate(self, market_data: Dict) -> Dict:
        order_book = market_data.get("order_book", {})
        trades = market_data.get("trades", {})
        bid_size = float(order_book.get("bid_volume", 0) or 0)
        ask_size = float(order_book.get("ask_volume", 0) or 0)
        buy_volume = float(trades.get("buy_volume", 0) or 0)
        sell_volume = float(trades.get("sell_volume", 0) or 0)

        imbalance = (bid_size - ask_size) / max(bid_size + ask_size, 1e-6)
        trade_imbalance = (buy_volume - sell_volume) / max(buy_volume + sell_volume, 1e-6)

        return {
            "order_book_imbalance": imbalance,
            "trade_flow_imbalance": trade_imbalance,
            "liquidity_depth": float(order_book.get("depth", 0) or 0),
        }


@dataclass(slots=True)
class CrossAssetFeatureEngine:
    """Cross-asset correlation and contagion features."""

    async def generate(self, market_data: Dict) -> Dict:
        correlations = market_data.get("cross_asset_correlations", {})
        volatility_spillover = market_data.get("volatility_spillover", 0.0)
        risk_premium = market_data.get("risk_premium_arbitrage", 0.0)

        avg_corr = sum(correlations.values()) / max(len(correlations), 1)
        return {
            "avg_cross_asset_correlation": avg_corr,
            "volatility_spillover": float(volatility_spillover),
            "risk_premium_arbitrage": float(risk_premium),
        }


@dataclass(slots=True)
class MacroFeatureEngine:
    """Macro-economic regime features."""

    async def generate(self, market_data: Dict) -> Dict:
        macro = market_data.get("macro", {})
        return {
            "macro_growth": float(macro.get("growth", 0) or 0),
            "macro_inflation": float(macro.get("inflation", 0) or 0),
            "macro_employment": float(macro.get("employment", 0) or 0),
        }


@dataclass(slots=True)
class AlternativeDataEngine:
    """Alternative data sources (sentiment, news, etc.)."""

    async def generate(self, market_data: Dict) -> Dict:
        sentiment = market_data.get("sentiment", {})
        return {
            "news_sentiment": float(sentiment.get("news", 0) or 0),
            "social_sentiment": float(sentiment.get("social", 0) or 0),
            "onchain_sentiment": float(sentiment.get("onchain", 0) or 0),
        }


@dataclass(slots=True)
class AdvancedFeatureEngine:
    """Aggregate feature generators for model consumption."""

    market_microstructure: MarketMicrostructureEngine = field(default_factory=MarketMicrostructureEngine)
    cross_asset: CrossAssetFeatureEngine = field(default_factory=CrossAssetFeatureEngine)
    macro: MacroFeatureEngine = field(default_factory=MacroFeatureEngine)
    alternative: AlternativeDataEngine = field(default_factory=AlternativeDataEngine)

    async def generate_features(self, raw_data: Dict) -> Dict:
        features = {}
        features.update(await self.market_microstructure.generate(raw_data))
        features.update(await self.cross_asset.generate(raw_data))
        features.update(await self.macro.generate(raw_data))
        features.update(await self.alternative.generate(raw_data))
        return features

