"""
Funding rate and basis analysis for perpetual futures.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np

logger = logging.getLogger(__name__)


class AdvancedFundingEngine:
    """Evaluates funding regimes, arbitrage opportunities, and carry trades."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        funding_rates = market_data.get("funding_rates", {})
        spot_prices = market_data.get("spot_prices", market_data.get("prices", {}))
        futures_prices = market_data.get("futures_prices", {})

        if not funding_rates or not spot_prices or not futures_prices:
            return self._error("missing_funding_inputs")

        regimes = self._regime_analysis(funding_rates)
        arbitrage = self._arbitrage_opportunities(funding_rates, spot_prices, futures_prices)
        carry = self._carry_analysis(funding_rates, spot_prices)
        predictability = self._predictability(funding_rates)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "funding_regimes": regimes,
            "arbitrage_opportunities": arbitrage,
            "carry_trade_analysis": carry,
            "funding_predictability": predictability,
        }

    def _regime_analysis(self, funding_rates: Dict[str, Any]) -> Dict[str, Any]:
        regimes: Dict[str, Any] = {}
        for symbol, history in funding_rates.items():
            if isinstance(history, list) and history:
                rate = history[-1]
            else:
                rate = float(history)
            if rate > 0.0005:
                regime = "long_crowded"
            elif rate < -0.0005:
                regime = "short_crowded"
            else:
                regime = "balanced"
            regimes[symbol] = {"current_rate": float(rate), "regime": regime}
        return regimes

    def _arbitrage_opportunities(self, funding: Dict[str, Any], spot: Dict[str, Any], futures: Dict[str, Any]) -> Dict[str, Any]:
        opportunities: Dict[str, Any] = {"profitable": 0}
        for symbol, rate in funding.items():
            if isinstance(rate, list):
                current_rate = rate[-1]
            else:
                current_rate = rate
            spot_price = self._latest_price(spot.get(symbol))
            futures_price = self._latest_price(futures.get(symbol))
            if spot_price is None or futures_price is None or spot_price == 0:
                continue
            basis = (futures_price - spot_price) / spot_price
            theoretical = basis * 3 * 365  # approx annualised with 8h funding
            mispricing = current_rate - theoretical
            opportunity = abs(mispricing) > 0.002
            if opportunity:
                opportunities["profitable"] += 1
            opportunities[symbol] = {
                "current_funding": float(current_rate),
                "theoretical_funding": float(theoretical),
                "funding_mispricing": float(mispricing),
                "arbitrage_opportunity": opportunity,
                "direction": "short_perp_long_spot" if mispricing > 0 else "long_perp_short_spot",
            }
        return opportunities

    def _carry_analysis(self, funding: Dict[str, Any], spot: Dict[str, Any]) -> Dict[str, Any]:
        carry: Dict[str, Any] = {}
        for symbol, rate in funding.items():
            current_rate = rate[-1] if isinstance(rate, list) and rate else rate
            volatility = self._estimate_volatility(spot.get(symbol))
            annualised = float(current_rate) * 3 * 365
            risk_adjusted = annualised / (volatility + 1e-6)
            carry[symbol] = {
                "annualised_carry": annualised,
                "volatility": volatility,
                "risk_adjusted_carry": risk_adjusted,
            }
        return carry

    def _predictability(self, funding: Dict[str, Any]) -> Dict[str, Any]:
        predictions: Dict[str, Any] = {}
        for symbol, history in funding.items():
            series = np.array(history[-24:]) if isinstance(history, list) else np.array([history])
            if len(series) < 5:
                continue
            trend = np.polyfit(np.arange(len(series)), series, 1)[0]
            volatility = np.std(series)
            prediction = float(series[-1] + trend)
            confidence = float(max(0.1, min(1.0, 1.0 / (volatility + 1e-6))))
            predictions[symbol] = {"next_funding_estimate": prediction, "confidence": confidence}
        return predictions

    @staticmethod
    def _latest_price(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, list) and value:
            return float(value[-1])
        if isinstance(value, (int, float)):
            return float(value)
        return None

    @staticmethod
    def _estimate_volatility(prices: Any) -> float:
        if prices is None:
            return 0.0
        if isinstance(prices, list) and len(prices) > 1:
            returns = np.diff(np.log(np.maximum(prices, 1e-9)))
            return float(np.std(returns) * np.sqrt(252))
        return 0.0

    @staticmethod
    def _error(reason: str) -> Dict[str, Any]:
        return {
            "error": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "funding_regimes": {},
            "arbitrage_opportunities": {},
            "carry_trade_analysis": {},
            "funding_predictability": {},
        }

