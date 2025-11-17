"""Regime type definitions and data structures."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class MarketRegime(Enum):
    TRENDING_BULL = "trending_bull"
    TRENDING_BEAR = "trending_bear"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRASH = "crash"
    RALLY = "rally"


@dataclass(slots=True)
class MarketState:
    timestamp: float
    regime: MarketRegime
    features: Dict[str, float]
    volatility_regime: str
    liquidity_state: str
    cross_asset_correlations: Dict[str, float]

