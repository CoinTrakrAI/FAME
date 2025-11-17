"""Volatility regime detection utilities."""

from __future__ import annotations

import logging
from statistics import mean, stdev
from typing import Dict, Iterable

from regimes.regime_types import MarketRegime

logger = logging.getLogger(__name__)


class SimpleVolatilityModel:
    """Fallback volatility detector using historical returns."""

    def __init__(self, window_short: int = 20, window_long: int = 60) -> None:
        self.window_short = window_short
        self.window_long = window_long

    async def detect_regime(self, market_data: Dict) -> MarketRegime:
        returns = market_data.get("returns")
        if not returns:
            return MarketRegime.RANGING
        if len(returns) < self.window_short:
            return MarketRegime.RANGING
        short_vol = self._annualised_vol(returns[-self.window_short :])
        long_vol = self._annualised_vol(returns[-self.window_long :]) if len(returns) >= self.window_long else short_vol

        if short_vol > long_vol * 1.5:
            return MarketRegime.HIGH_VOLATILITY
        if short_vol < long_vol * 0.5:
            return MarketRegime.LOW_VOLATILITY
        return MarketRegime.RANGING

    def _annualised_vol(self, returns: Iterable[float]) -> float:
        try:
            return float(stdev(returns)) * (252**0.5)
        except Exception:
            return 0.0


class GARCHVolatilityModel:
    """Placeholder for GARCH-based volatility detection."""

    def __init__(self) -> None:
        self.simple = SimpleVolatilityModel()

    async def detect_regime(self, market_data: Dict) -> MarketRegime:
        # TODO: integrate actual GARCH modelling
        return await self.simple.detect_regime(market_data)

