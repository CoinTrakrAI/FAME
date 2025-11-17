"""
Sharpe and risk-adjusted performance intelligence.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AdvancedSharpeEngine:
    """Analyses Sharpe ratios across multiple horizons and stability metrics."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._risk_free = float(self.config.get("risk_free_rate", 0.01)) / 252

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        returns = self._extract_returns(market_data)
        if returns.empty:
            return self._error_result("insufficient_returns")

        multi = self._multi_timeframe_sharpe(returns)
        probabilistic = self._probabilistic_sharpe(returns)
        stability = self._stability_metric(multi)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "multi_timeframe_sharpe": multi,
            "probabilistic_sharpe": probabilistic,
            "stability_score": stability,
            "data_quality_score": self._data_quality(returns),
        }

    def _extract_returns(self, market_data: Dict[str, Any]) -> pd.Series:
        if "returns" in market_data:
            data = market_data["returns"]
            if isinstance(data, pd.Series):
                return data.dropna()
            if isinstance(data, list):
                return pd.Series(data).dropna()
        prices = market_data.get("prices")
        if not prices:
            return pd.Series(dtype=float)
        df = prices if isinstance(prices, pd.DataFrame) else pd.DataFrame(prices)
        df = df.sort_index()
        return df.pct_change().mean(axis=1).dropna()

    def _multi_timeframe_sharpe(self, returns: pd.Series) -> Dict[str, Dict[str, float]]:
        frames = {"daily": 1, "weekly": 5, "monthly": 21, "quarterly": 63, "annually": 252}
        metrics: Dict[str, Dict[str, float]] = {}
        for name, window in frames.items():
            if len(returns) < window * 2:
                continue
            resampled = returns.rolling(window).sum().dropna()
            sharpe = self._sharpe_ratio(resampled)
            metrics[name] = {
                "sharpe_ratio": sharpe,
                "mean_return": float(resampled.mean()),
                "volatility": float(resampled.std()),
                "observations": len(resampled),
            }
        return metrics

    def _probabilistic_sharpe(self, returns: pd.Series, simulations: int = 2000) -> Dict[str, float]:
        observed = self._sharpe_ratio(returns)
        mu, sigma = float(returns.mean()), float(returns.std(ddof=1))
        if sigma == 0 or len(returns) < 5:
            return {"observed_sharpe": observed, "probability_skill": 0.5}

        simulated = np.random.normal(mu, sigma, size=(simulations, len(returns)))
        simulated_sharpes = np.array([self._sharpe_ratio(sim) for sim in simulated])
        prob_skill = float(np.mean(simulated_sharpes < observed))
        return {
            "observed_sharpe": observed,
            "probability_skill": prob_skill,
            "skill_threshold_95": float(np.percentile(simulated_sharpes, 95)),
        }

    def _stability_metric(self, sharpe_metrics: Dict[str, Dict[str, float]]) -> float:
        ratios = [metrics["sharpe_ratio"] for metrics in sharpe_metrics.values()]
        if not ratios:
            return 0.5
        return float(1.0 - (np.std(ratios) / (abs(np.mean(ratios)) + 1e-6)))

    def _sharpe_ratio(self, returns: Any) -> float:
        series = pd.Series(returns).dropna()
        if series.empty:
            return 0.0
        excess = series - self._risk_free
        vol = excess.std(ddof=1)
        if vol == 0:
            return 0.0
        return float(np.sqrt(252) * excess.mean() / vol)

    @staticmethod
    def _data_quality(returns: pd.Series) -> float:
        if returns.empty:
            return 0.0
        return float(min(1.0, len(returns) / 500))

    @staticmethod
    def _error_result(reason: str) -> Dict[str, Any]:
        return {
            "error": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "multi_timeframe_sharpe": {},
            "probabilistic_sharpe": {},
            "stability_score": 0.0,
            "data_quality_score": 0.0,
        }

