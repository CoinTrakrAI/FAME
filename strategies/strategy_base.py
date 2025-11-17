"""Base strategy definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol

from regimes.regime_types import MarketRegime


@dataclass(slots=True)
class TradingSignal:
    asset: str
    direction: float  # -1 to 1
    confidence: float
    size: float
    strategy: str
    expected_hold_hours: float


class Strategy(Protocol):
    name: str

    def is_suitable_for_regime(self, regime: MarketRegime) -> bool:
        ...

    async def generate_signals(self, market_data: Dict, regime: MarketRegime) -> Dict[str, TradingSignal]:
        ...

