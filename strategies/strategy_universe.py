"""Strategy universe for different asset classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Type

from regimes.regime_types import MarketRegime
from strategies.basic_strategies import MarketMakingStrategy, MeanReversionStrategy, MomentumTrendStrategy
from strategies.strategy_base import Strategy


@dataclass(slots=True)
class StrategyUniverse:
    """Registry of strategy instances."""

    strategy_classes: Dict[str, Type[Strategy]] = field(
        default_factory=lambda: {
            "momentum_trend": MomentumTrendStrategy,
            "mean_reversion": MeanReversionStrategy,
            "market_making": MarketMakingStrategy,
        }
    )
    _instances: Dict[str, Strategy] = field(default_factory=dict, init=False)

    def get_strategies(self) -> Dict[str, Strategy]:
        if not self._instances:
            for name, cls in self.strategy_classes.items():
                self._instances[name] = cls()
        return self._instances

    def suitable_strategies(self, regime: MarketRegime) -> Dict[str, Strategy]:
        return {name: strat for name, strat in self.get_strategies().items() if strat.is_suitable_for_regime(regime)}

