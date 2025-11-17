"""Basic strategy skeletons."""

from __future__ import annotations

from typing import Dict

from regimes.regime_types import MarketRegime
from strategies.strategy_base import Strategy, TradingSignal


class MomentumTrendStrategy:
    name = "momentum_trend"

    def is_suitable_for_regime(self, regime: MarketRegime) -> bool:
        return regime in {MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR}

    async def generate_signals(self, market_data: Dict, regime: MarketRegime) -> Dict[str, TradingSignal]:
        signals: Dict[str, TradingSignal] = {}
        momentum = market_data.get("momentum", {})
        for asset, value in momentum.items():
            direction = 1.0 if value > 0 else -1.0
            confidence = min(abs(value), 1.0)
            signals[asset] = TradingSignal(
                asset=asset,
                direction=direction if regime == MarketRegime.TRENDING_BULL else -direction,
                confidence=confidence,
                size=0.05 * confidence,
                strategy=self.name,
                expected_hold_hours=24.0,
            )
        return signals


class MeanReversionStrategy:
    name = "mean_reversion"

    def is_suitable_for_regime(self, regime: MarketRegime) -> bool:
        return regime in {MarketRegime.RANGING, MarketRegime.LOW_VOLATILITY}

    async def generate_signals(self, market_data: Dict, regime: MarketRegime) -> Dict[str, TradingSignal]:
        signals: Dict[str, TradingSignal] = {}
        zscores = market_data.get("zscores", {})
        for asset, z in zscores.items():
            if abs(z) < 1.0:
                continue
            direction = -1.0 if z > 0 else 1.0
            confidence = min(abs(z) / 3.0, 1.0)
            signals[asset] = TradingSignal(
                asset=asset,
                direction=direction,
                confidence=confidence,
                size=0.03 * confidence,
                strategy=self.name,
                expected_hold_hours=8.0,
            )
        return signals


class MarketMakingStrategy:
    name = "market_making"

    def is_suitable_for_regime(self, regime: MarketRegime) -> bool:
        return regime in {MarketRegime.RANGING, MarketRegime.LOW_VOLATILITY}

    async def generate_signals(self, market_data: Dict, regime: MarketRegime) -> Dict[str, TradingSignal]:
        signals: Dict[str, TradingSignal] = {}
        spreads = market_data.get("spreads", {})
        liquidity = market_data.get("liquidity", {})
        for asset, spread in spreads.items():
            depth = liquidity.get(asset, 0.0)
            if depth <= 0:
                continue
            confidence = min(max(0.0, 1.0 - spread / 0.01), 1.0)
            signals[asset] = TradingSignal(
                asset=asset,
                direction=0.0,
                confidence=confidence,
                size=0.02 * confidence,
                strategy=self.name,
                expected_hold_hours=1.0,
            )
        return signals

