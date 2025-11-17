"""
Regime shift detection using statistical indicators.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AdvancedRegimeShiftEngine:
    """Detects market regimes, stability, and transition risk indicators."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._history: Dict[str, list[str]] = {}

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        prices = market_data.get("prices")
        if not prices:
            return self._error("missing_prices")
        df = prices if isinstance(prices, pd.DataFrame) else pd.DataFrame(prices)
        df = df.sort_index()
        if df.shape[0] < 30:
            return self._error("insufficient_history")

        returns = df.pct_change().dropna()
        factors = self._compute_factors(returns)
        current_regime = self._classify_regime(factors)
        stability = self._stability_assessment(factors, current_regime["type"])
        early_warnings = self._early_warning_signals(factors)
        transition_probs = self._transition_probabilities(current_regime["type"])

        timestamp = datetime.now(timezone.utc).isoformat()
        self._history.setdefault("regimes", []).append(current_regime["type"])
        if len(self._history["regimes"]) > 500:
            self._history["regimes"] = self._history["regimes"][-250:]

        return {
            "timestamp": timestamp,
            "current_regime": current_regime,
            "regime_stability": stability,
            "early_warnings": early_warnings,
            "transition_probabilities": transition_probs,
            "historical_regimes": self._history["regimes"][-20:],
        }

    def _compute_factors(self, returns: pd.DataFrame) -> Dict[str, float]:
        market = returns.mean(axis=1)
        vol = float(market.std() * np.sqrt(252))
        skew = float(pd.Series(market).skew())
        kurt = float(pd.Series(market).kurtosis())
        trend = float(np.polyfit(np.arange(len(market)), market.cumsum(), 1)[0])
        drawdown = float((1 + market).cumprod().cummax() - (1 + market).cumprod()).max()
        return {"volatility": vol, "skew": skew, "kurtosis": kurt, "trend": trend, "drawdown": drawdown}

    def _classify_regime(self, factors: Dict[str, float]) -> Dict[str, Any]:
        vol = factors["volatility"]
        trend = factors["trend"]

        if vol > 0.6:
            regime = "high_volatility"
        elif vol < 0.2 and trend > 0.0:
            regime = "trending_bull"
        elif vol < 0.2 and trend < 0.0:
            regime = "trending_bear"
        elif abs(trend) < 0.001:
            regime = "ranging"
        else:
            regime = "normal"
        return {"type": regime, "factors": factors}

    def _stability_assessment(self, factors: Dict[str, float], regime: str) -> Dict[str, float]:
        volatility_stability = float(max(0.0, 1.0 - min(1.0, factors["volatility"])))
        trend_stability = float(max(0.0, 1.0 - min(1.0, abs(factors["trend"]) * 100)))
        skew_risk = float(min(1.0, abs(factors["skew"])))
        composite = (volatility_stability * 0.4) + (trend_stability * 0.4) + ((1 - skew_risk) * 0.2)
        return {
            "stability_score": composite,
            "volatility_stability": volatility_stability,
            "trend_stability": trend_stability,
            "skew_risk": skew_risk,
            "regime": regime,
        }

    def _early_warning_signals(self, factors: Dict[str, float]) -> Dict[str, Any]:
        warnings: Dict[str, Any] = {}
        if factors["volatility"] > 0.5:
            warnings["volatility_warning"] = {"level": "high", "detail": "volatility rising sharply"}
        if factors["drawdown"] > 0.1:
            warnings["drawdown_warning"] = {"level": "medium", "detail": "recent drawdown elevated"}
        if abs(factors["skew"]) > 0.5:
            warnings["skew_warning"] = {"level": "medium", "detail": "return distribution skewed"}

        composite_score = min(1.0, 0.3 * (factors["volatility"] / 0.4) + 0.3 * (factors["drawdown"] / 0.1) + 0.4 * abs(factors["skew"]))
        warnings["composite_early_warning"] = {"score": composite_score, "confidence": 1 - abs(0.5 - composite_score)}
        return warnings

    def _transition_probabilities(self, current_regime: str) -> Dict[str, float]:
        transitions = {"normal": 0.6, "high_volatility": 0.2, "trending_bull": 0.1, "trending_bear": 0.1}
        if current_regime == "high_volatility":
            transitions = {"high_volatility": 0.5, "normal": 0.3, "ranging": 0.2}
        elif current_regime == "trending_bull":
            transitions = {"trending_bull": 0.5, "normal": 0.3, "high_volatility": 0.2}
        transitions["ensemble_max"] = max(transitions.values())
        return transitions

    @staticmethod
    def _error(reason: str) -> Dict[str, Any]:
        return {
            "error": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_regime": {"type": "unknown"},
            "regime_stability": {"stability_score": 0.0},
            "early_warnings": {},
            "transition_probabilities": {},
        }

