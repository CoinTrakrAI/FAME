"""Cross-asset correlation analysis."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

from regimes.regime_types import MarketRegime


class CrossAssetCorrelationEngine:
    """Analyse correlation structures between assets."""

    async def analyze(self, market_data: Dict) -> MarketRegime:
        correlations = market_data.get("cross_asset_correlations", {})
        if not correlations:
            return MarketRegime.RANGING
        avg_corr = sum(correlations.values()) / max(len(correlations), 1)
        if avg_corr > 0.7:
            return MarketRegime.CRASH
        if avg_corr < 0.2:
            return MarketRegime.RALLY
        return MarketRegime.RANGING

