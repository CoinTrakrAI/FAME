"""Macro regime classification."""

from __future__ import annotations

from typing import Dict

from regimes.regime_types import MarketRegime


class MacroRegimeClassifier:
    """Classify macro-economic regime from indicators."""

    async def classify(self, market_data: Dict) -> MarketRegime:
        macro = market_data.get("macro", {})
        growth = macro.get("growth", 0)
        inflation = macro.get("inflation", 0)
        if growth > 0 and inflation < 0:
            return MarketRegime.RALLY
        if growth < 0 and inflation > 0:
            return MarketRegime.CRASH
        if abs(growth) < 0.5 and abs(inflation) < 0.5:
            return MarketRegime.RANGING
        return MarketRegime.TRENDING_BULL if growth > 0 else MarketRegime.TRENDING_BEAR

