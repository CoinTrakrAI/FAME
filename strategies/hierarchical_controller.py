"""Hierarchical strategy controller."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from regimes.regime_engine import RegimeDetectionEngine
from regimes.regime_types import MarketRegime
from strategies.strategy_base import TradingSignal
from strategies.strategy_universe import StrategyUniverse


@dataclass(slots=True)
class MetaStrategyAllocator:
    """Assign weights to strategies for a given regime."""

    default_weights: Dict[MarketRegime, Dict[str, float]] = field(
        default_factory=lambda: {
            MarketRegime.TRENDING_BULL: {"momentum_trend": 0.6, "market_making": 0.2, "mean_reversion": 0.2},
            MarketRegime.TRENDING_BEAR: {"momentum_trend": 0.6, "market_making": 0.2, "mean_reversion": 0.2},
            MarketRegime.RANGING: {"mean_reversion": 0.5, "market_making": 0.4, "momentum_trend": 0.1},
            MarketRegime.HIGH_VOLATILITY: {"momentum_trend": 0.4, "mean_reversion": 0.3, "market_making": 0.3},
            MarketRegime.LOW_VOLATILITY: {"market_making": 0.5, "mean_reversion": 0.4, "momentum_trend": 0.1},
            MarketRegime.CRASH: {"momentum_trend": 0.7, "market_making": 0.2, "mean_reversion": 0.1},
            MarketRegime.RALLY: {"momentum_trend": 0.7, "market_making": 0.2, "mean_reversion": 0.1},
        }
    )

    def get_weights(self, regime: MarketRegime) -> Dict[str, float]:
        return self.default_weights.get(regime, self.default_weights[MarketRegime.RANGING])


@dataclass(slots=True)
class HierarchicalStrategyController:
    regime_detector: RegimeDetectionEngine = field(default_factory=RegimeDetectionEngine)
    strategy_universe: StrategyUniverse = field(default_factory=StrategyUniverse)
    allocator: MetaStrategyAllocator = field(default_factory=MetaStrategyAllocator)

    async def decide_action(
        self,
        market_data: Dict,
        regime_override: Optional[MarketRegime] = None,
        strategy_confidence: Optional[Dict[str, float]] = None,
    ) -> Tuple[MarketRegime, Dict[str, TradingSignal], Dict[str, float]]:
        regime = regime_override or await self.regime_detector.analyze(market_data)
        strategies = self.strategy_universe.suitable_strategies(regime)
        base_weights = self.allocator.get_weights(regime)
        confidence_map = strategy_confidence or {}

        adjusted_weights: Dict[str, float] = {}
        for name in strategies.keys():
            confidence = confidence_map.get(name, 1.0)
            adjusted_weights[name] = max(0.0, base_weights.get(name, 0.0) * confidence)

        total = sum(adjusted_weights.values())
        if total > 0:
            adjusted_weights = {name: weight / total for name, weight in adjusted_weights.items()}
        else:
            adjusted_weights = base_weights

        combined: Dict[str, TradingSignal] = {}
        for name, strategy in strategies.items():
            signals = await strategy.generate_signals(market_data, regime)
            weight = adjusted_weights.get(name, 0.0)
            for asset, signal in signals.items():
                if asset not in combined:
                    combined[asset] = signal
                    combined[asset].size *= weight
                    combined[asset].confidence *= weight
                else:
                    existing = combined[asset]
                    existing.direction = (existing.direction + signal.direction * weight) / 2.0
                    existing.size += signal.size * weight
                    existing.confidence = min(1.0, existing.confidence + signal.confidence * weight)
        return regime, combined, adjusted_weights

