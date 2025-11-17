"""
Open interest landscape analysis for options markets.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AdvancedOpenInterestEngine:
    """Analyses option open interest for concentration, money flow, and gamma exposure."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._top_n = int(self.config.get("top_strikes", 5))

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        oi = market_data.get("open_interest")
        if oi is None:
            oi = market_data.get("options_data")  # reuse chain if structured similarly
        if oi is None:
            return self._error("missing_open_interest")

        try:
            df = self._to_dataframe(oi)
        except ValueError as exc:
            return self._error(str(exc))

        concentration = self._concentration(df)
        money_flow = self._money_flow(df)
        gamma = self._gamma_exposure(df, market_data.get("prices", {}))
        smart_money = self._smart_money_flow(df)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "concentration_analysis": concentration,
            "money_flow": money_flow,
            "gamma_exposure": gamma,
            "smart_money_analysis": smart_money,
            "liquidity_score": float(min(1.0, df.get("call_oi", pd.Series()).mean() / 10_000)),
            "total_concentration": concentration.get("total_concentration", 0.0),
        }

    def _to_dataframe(self, data: Any) -> pd.DataFrame:
        if isinstance(data, pd.DataFrame):
            df = data.copy()
        else:
            df = pd.DataFrame(data)
        required = {"strike", "expiry", "call_oi", "put_oi"}
        if not required.issubset(df.columns):
            raise ValueError("invalid_open_interest_structure")
        return df

    def _concentration(self, df: pd.DataFrame) -> Dict[str, Any]:
        grouped = df.groupby("expiry")
        results: Dict[str, Any] = {}
        total_concentration = 0.0

        for expiry, subset in grouped:
            calls = subset.nlargest(self._top_n, "call_oi")
            puts = subset.nlargest(self._top_n, "put_oi")
            total_calls = subset["call_oi"].sum() or 1.0
            total_puts = subset["put_oi"].sum() or 1.0

            call_ratio = float(calls["call_oi"].sum() / total_calls)
            put_ratio = float(puts["put_oi"].sum() / total_puts)
            total_ratio = float((calls["call_oi"].sum() + puts["put_oi"].sum()) / (total_calls + total_puts))

            results[str(expiry)] = {
                "call_wall": float(calls["strike"].iloc[0]) if not calls.empty else None,
                "put_wall": float(puts["strike"].iloc[0]) if not puts.empty else None,
                "call_concentration": call_ratio,
                "put_concentration": put_ratio,
                "total_concentration": total_ratio,
            }
            total_concentration = max(total_concentration, total_ratio)

        results["total_concentration"] = total_concentration
        return results

    def _money_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        if "timestamp" not in df.columns:
            return {"warning": "no_timestamp"}
        sorted_df = df.sort_values("timestamp")
        recent = sorted_df.groupby("timestamp")[["call_oi", "put_oi"]].sum().diff().iloc[-1]
        return {
            "call_flow": float(recent.get("call_oi", 0.0)),
            "put_flow": float(recent.get("put_oi", 0.0)),
            "net_flow": float(recent.get("call_oi", 0.0) - recent.get("put_oi", 0.0)),
        }

    def _gamma_exposure(self, df: pd.DataFrame, prices: Dict[str, Any]) -> Dict[str, Any]:
        if "gamma" not in df.columns or not prices:
            return {"warning": "missing_gamma_data"}
        current_price = np.mean([v[-1] if isinstance(v, list) else v for v in prices.values() if v]) or 0.0
        df = df.copy()
        df["total_gamma"] = df["gamma"] * (df["call_oi"] - df["put_oi"])
        gamma_profile = (
            df.groupby("strike")["total_gamma"].sum().sort_index().to_dict()
        )
        flip_level = min(gamma_profile, key=lambda strike: abs(gamma_profile[strike])) if gamma_profile else None
        return {
            "total_gamma": float(df["total_gamma"].sum()),
            "gamma_profile": gamma_profile,
            "gamma_flip_level": float(flip_level) if flip_level is not None else None,
            "distance_to_flip": abs(current_price - float(flip_level)) if flip_level and current_price else None,
        }

    def _smart_money_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        df = df.copy()
        df["premium"] = df.get("call_oi", 0) * df.get("call_price", 0) + df.get("put_oi", 0) * df.get("put_price", 0)
        top_flows = df.nlargest(self._top_n, "premium")
        return {
            "top_strikes": top_flows[["strike", "premium"]].to_dict(orient="records"),
            "total_premium": float(df["premium"].sum()),
        }

    @staticmethod
    def _error(reason: str) -> Dict[str, Any]:
        return {
            "error": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "concentration_analysis": {},
            "money_flow": {},
            "gamma_exposure": {},
            "smart_money_analysis": {},
        }

