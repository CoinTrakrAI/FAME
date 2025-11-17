"""Transformer-based regime predictor placeholder."""

from __future__ import annotations

from typing import Dict

from regimes.regime_types import MarketRegime


class RegimeTransformer:
    """Stub for transformer model predicting market regime."""

    def predict(self, market_data: Dict) -> MarketRegime:
        # TODO: integrate actual transformer model
        return MarketRegime.RANGING

