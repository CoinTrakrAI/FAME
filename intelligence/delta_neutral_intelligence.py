"""
Delta neutral and Greek exposure analytics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np

logger = logging.getLogger(__name__)


class AdvancedDeltaNeutralEngine:
    """Analyses option chains to estimate Greek exposures and hedging recommendations."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        options_data = market_data.get("options_data", {})
        underlying_prices = market_data.get("prices", {})

        if not options_data or not underlying_prices:
            return self._fallback("missing_options_data")

        exposures = self._aggregate_greeks(options_data)
        hedging = self._hedging_recommendations(exposures)
        gamma_scalping = self._gamma_scalping_signal(exposures, underlying_prices)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "aggregate_exposure": exposures,
            "hedging_recommendations": hedging,
            "gamma_scalping": gamma_scalping,
            "data_quality_score": self._quality_score(options_data),
        }

    def _aggregate_greeks(self, options_data: Dict[str, Any]) -> Dict[str, float]:
        totals = {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}
        total_notional = 0.0
        for symbol, chain in options_data.items():
            for option in chain:
                size = float(option.get("open_interest", 0))
                notional = float(option.get("mark_price", 0)) * size
                total_notional += notional
                totals["delta"] += float(option.get("delta", 0.0)) * size
                totals["gamma"] += float(option.get("gamma", 0.0)) * size
                totals["vega"] += float(option.get("vega", 0.0)) * size
                totals["theta"] += float(option.get("theta", 0.0)) * size
                totals["rho"] += float(option.get("rho", 0.0)) * size

        totals["notional"] = total_notional
        return totals

    def _hedging_recommendations(self, exposures: Dict[str, float]) -> Dict[str, Any]:
        delta = exposures.get("delta", 0.0)
        gamma = exposures.get("gamma", 0.0)
        recs: Dict[str, Any] = {"delta_hedge": 0.0, "gamma_adjustment": 0.0, "priority": "low"}

        if abs(delta) > 1_000:
            recs["delta_hedge"] = -delta
            recs["priority"] = "high"
        elif abs(delta) > 100:
            recs["delta_hedge"] = -delta
            recs["priority"] = "medium"

        if abs(gamma) > 500:
            recs["gamma_adjustment"] = -gamma

        return recs

    def _gamma_scalping_signal(self, exposures: Dict[str, float], underlying_prices: Dict[str, Any]) -> Dict[str, Any]:
        gamma = exposures.get("gamma", 0.0)
        theta = exposures.get("theta", 0.0)
        notional = exposures.get("notional", 1.0) or 1.0
        implied_move = np.sqrt(abs(gamma) / max(notional, 1.0))
        theta_cost = theta / max(notional, 1.0)
        profitable = implied_move > abs(theta_cost)
        return {"breakeven_move": implied_move, "theta_cost": theta_cost, "profitable": profitable}

    @staticmethod
    def _quality_score(options_data: Dict[str, Any]) -> float:
        count = sum(len(chain) for chain in options_data.values())
        return float(min(1.0, count / 500))

    def _fallback(self, reason: str) -> Dict[str, Any]:
        return {
            "error": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "aggregate_exposure": {},
            "hedging_recommendations": {},
            "gamma_scalping": {},
            "data_quality_score": 0.0,
        }

