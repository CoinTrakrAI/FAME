"""Ensemble market regime detection engine."""

from __future__ import annotations

import collections
from typing import Dict, List

from regimes.regime_types import MarketRegime
from regimes.volatility import GARCHVolatilityModel
from regimes.correlations import CrossAssetCorrelationEngine
from regimes.macro import MacroRegimeClassifier
from regimes.transformer import RegimeTransformer


class RegimeDetectionEngine:
    """Combine multiple detectors to infer market regime."""

    def __init__(self) -> None:
        self.volatility_model = GARCHVolatilityModel()
        self.correlation_engine = CrossAssetCorrelationEngine()
        self.macro_classifier = MacroRegimeClassifier()
        self.transformer_model = RegimeTransformer()

    async def analyze(self, market_data: Dict) -> MarketRegime:
        votes: List[MarketRegime] = []
        votes.append(await self.volatility_model.detect_regime(market_data))
        votes.append(await self.correlation_engine.analyze(market_data))
        votes.append(await self.macro_classifier.classify(market_data))
        votes.append(self.transformer_model.predict(market_data))

        counter = collections.Counter(votes)
        return counter.most_common(1)[0][0]

