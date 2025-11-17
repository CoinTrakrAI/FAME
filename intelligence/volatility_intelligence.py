"""
Advanced volatility intelligence with regime detection and clustering metrics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AdvancedVolatilityEngine:
    """Computes volatility regimes, clustering, and risk-premium analytics."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._lookback = int(self.config.get("lookback", 252))
        self._short_window = int(self.config.get("short_window", 20))
        self._long_window = int(self.config.get("long_window", 60))

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        prices = market_data.get("prices")
        if not prices:
            return self._error_result("missing_price_data")

        df = self._to_dataframe(prices)
        returns = df.pct_change().dropna(how="all")
        if returns.empty:
            return self._error_result("insufficient_data")

        vol_metrics = self._volatility_metrics(returns)
        clustering = self._volatility_clustering(returns)
        vrp = self._volatility_risk_premium(df, returns)

        regime, regime_probs = self._detect_regime(vol_metrics)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_regime": regime,
            "regime_probabilities": regime_probs,
            "regime_stability": 1.0 - regime_probs.get("high_vol", 0.0),
            "volatility_metrics": vol_metrics,
            "clustering_metrics": clustering,
            "vrp_analysis": vrp,
            "stability_score": 1.0 - regime_probs.get("high_vol", 0.0),
            "data_quality_score": self._data_quality_score(returns),
        }

    @staticmethod
    def _to_dataframe(prices: Dict[str, Any]) -> pd.DataFrame:
        if isinstance(prices, pd.DataFrame):
            return prices.copy()
        return pd.DataFrame(prices).sort_index()

    def _volatility_metrics(self, returns: pd.DataFrame) -> Dict[str, Any]:
        realized = returns.rolling(self._short_window).std() * np.sqrt(252)
        long_realized = returns.rolling(self._long_window).std() * np.sqrt(252)
        latest = realized.iloc[-1].fillna(0.0)
        long_latest = long_realized.iloc[-1].fillna(0.0)
        return {
            "short_term": latest.to_dict(),
            "medium_term": long_latest.to_dict(),
            "portfolio_volatility": float(np.nanmean(latest)),
            "volatility_trend": float(np.nanmean(latest - long_latest)),
        }

    def _volatility_clustering(self, returns: pd.DataFrame) -> Dict[str, Any]:
        squared_returns = returns ** 2
        acf_values = []
        for lag in range(1, 11):
            acf = squared_returns.apply(lambda series: series.autocorr(lag=lag))
            acf_values.append(float(acf.mean()) if not acf.isna().all() else 0.0)

        hurst_exponent = self._hurst_exponent(squared_returns.mean(axis=1))
        avg_duration = self._average_regime_duration(squared_returns.mean(axis=1))

        return {
            "volatility_autocorrelation": acf_values,
            "hurst_exponent": hurst_exponent,
            "average_regime_duration": avg_duration,
        }

    def _volatility_risk_premium(self, prices: pd.DataFrame, returns: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        realized_20 = returns.rolling(20).std() * np.sqrt(252)
        last_realized = realized_20.iloc[-1]
        vrp: Dict[str, Dict[str, float]] = {}
        for symbol in prices.columns:
            realised = float(last_realized.get(symbol, np.nan))
            implied = float(self._rough_implied_volatility(prices[symbol], window=20))
            vrp[symbol] = {
                "realized_volatility": realised,
                "implied_volatility": implied,
                "volatility_risk_premium": float(implied - realised),
            }
        return vrp

    def _detect_regime(self, vol_metrics: Dict[str, Any]) -> tuple[str, Dict[str, float]]:
        portfolio_vol = vol_metrics.get("portfolio_volatility", 0.0)
        trend = vol_metrics.get("volatility_trend", 0.0)

        if portfolio_vol > 0.6:
            regime = "high_volatility"
            probs = {"high_vol": 0.7, "normal": 0.2, "low_vol": 0.1}
        elif portfolio_vol < 0.2:
            regime = "low_volatility"
            probs = {"low_vol": 0.6, "normal": 0.3, "high_vol": 0.1}
        elif trend > 0.05:
            regime = "volatility_rising"
            probs = {"high_vol": 0.5, "normal": 0.4, "low_vol": 0.1}
        elif trend < -0.05:
            regime = "volatility_fading"
            probs = {"low_vol": 0.4, "normal": 0.5, "high_vol": 0.1}
        else:
            regime = "normal"
            probs = {"normal": 0.6, "high_vol": 0.2, "low_vol": 0.2}
        probs["ensemble_max"] = max(probs.values())
        return regime, probs

    @staticmethod
    def _hurst_exponent(series: pd.Series) -> float:
        if len(series.dropna()) < 20:
            return 0.5
        log_rs = []
        log_n = []
        for segment in range(10, min(200, len(series)), 10):
            subset = series.iloc[:segment].dropna()
            if subset.empty:
                continue
            mean = subset.mean()
            dev = subset - mean
            cumulative = dev.cumsum()
            R = cumulative.max() - cumulative.min()
            S = subset.std()
            if S == 0:
                continue
            log_rs.append(np.log(R / S))
            log_n.append(np.log(segment))
        if len(log_rs) < 2:
            return 0.5
        slope, _ = np.polyfit(log_n, log_rs, 1)
        return float(max(0.0, min(1.0, slope)))

    @staticmethod
    def _average_regime_duration(series: pd.Series, threshold: float = 0.0001) -> float:
        regime = series > threshold
        durations = []
        count = 0
        last_value = regime.iloc[0]
        for value in regime:
            if value == last_value:
                count += 1
            else:
                durations.append(count)
                count = 1
                last_value = value
        durations.append(count)
        return float(np.mean(durations)) if durations else 0.0

    @staticmethod
    def _rough_implied_volatility(price_series: pd.Series, window: int = 20) -> float:
        if len(price_series.dropna()) < window:
            return 0.3
        log_returns = np.log(price_series / price_series.shift(1)).dropna()
        return float(log_returns.rolling(window).std().iloc[-1] * np.sqrt(252))

    @staticmethod
    def _data_quality_score(returns: pd.DataFrame) -> float:
        if returns.empty:
            return 0.0
        missing = returns.isna().sum().sum() / (returns.shape[0] * returns.shape[1])
        observation_score = min(1.0, len(returns) / 250)
        return float(max(0.1, (1 - missing) * observation_score))

    @staticmethod
    def _error_result(reason: str) -> Dict[str, Any]:
        return {
            "error": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_regime": "unknown",
            "regime_probabilities": {"normal": 1.0},
            "data_quality_score": 0.0,
        }

