"""Portfolio-level risk orchestration."""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Dict, Iterable, List, Optional

try:  # numpy optional dependency
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore

from .advanced_metrics import (
    calculate_downside_deviation,
    calculate_expected_shortfall,
    calculate_liquidity_metrics,
    calculate_omega_ratio,
    calculate_parametric_var_cvar,
    generate_stress_scenarios,
)


@dataclass(slots=True)
class RiskConstraints:
    max_drawdown: float = 0.1
    max_leverage: float = 3.0
    max_position: float = 0.2


@dataclass(slots=True)
class RiskOrchestrator:
    constraints: RiskConstraints = field(default_factory=RiskConstraints)
    history_window: int = 252
    _returns_history: Deque[float] = field(init=False, repr=False)
    _latest_metrics: Dict[str, float] = field(default_factory=dict, init=False, repr=False)
    _metrics_history: Deque[Dict[str, float]] = field(init=False, repr=False)
    _horizon_windows: Dict[str, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._returns_history = deque(maxlen=self.history_window)
        self._metrics_history = deque(maxlen=max(self.history_window, 365))
        self._horizon_windows = {
            "1d": 1,
            "5d": 5,
            "21d": 21,
        }

    def apply(self, signals: Dict[str, float]) -> Dict[str, float]:
        clipped = {
            asset: max(min(size, self.constraints.max_position), -self.constraints.max_position)
            for asset, size in signals.items()
        }
        total = sum(abs(size) for size in clipped.values())
        if total > self.constraints.max_leverage > 0:
            scale = self.constraints.max_leverage / total
            clipped = {asset: size * scale for asset, size in clipped.items()}
        return clipped

    # ------------------------------------------------------------------ #
    # Advanced risk analytics helpers
    # ------------------------------------------------------------------ #

    def record_return(self, portfolio_return: float) -> None:
        """Record a portfolio return (decimal form, e.g. 0.01 for 1%)."""
        self._returns_history.append(float(portfolio_return))
        self._latest_metrics = self._compute_risk_metrics()
        self._store_metrics(self._latest_metrics)

    def extend_returns(self, returns: Iterable[float]) -> None:
        """Append multiple returns to history."""
        for value in returns:
            self.record_return(value)

    def clear_history(self) -> None:
        """Reset stored returns and metrics."""
        self._returns_history.clear()
        self._metrics_history.clear()
        self._latest_metrics = {}

    def risk_metrics(
        self,
        leverage: float = 1.0,
        positions: Optional[Dict[str, float]] = None,
        portfolio_value: Optional[float] = None,
    ) -> Dict[str, float]:
        """Return latest computed risk metrics, optionally adjusting for leverage."""
        if not self._latest_metrics:
            self._latest_metrics = self._compute_risk_metrics()
            self._store_metrics(self._latest_metrics)

        metrics = self._latest_metrics.copy()

        if positions:
            metrics.update(self._concentration_metrics(positions))
            if portfolio_value is not None:
                metrics.update(calculate_liquidity_metrics(positions, portfolio_value))

        if portfolio_value is not None:
            metrics["portfolio_value"] = float(portfolio_value)

        if leverage != 1.0:
            metrics["leverage"] = leverage
            for key in ("var_95", "var_99", "cvar_95", "cvar_99", "volatility"):
                metrics[key] = metrics[key] * leverage

        return metrics

    def _compute_risk_metrics(self) -> Dict[str, float]:
        if np is None or len(self._returns_history) < 2:
            return {
                "volatility": 0.0,
                "expected_return": 0.0,
                "var_95": 0.0,
                "var_99": 0.0,
                "cvar_95": 0.0,
                "cvar_99": 0.0,
                "current_drawdown": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "downside_deviation": 0.0,
                "omega_ratio": 0.0,
            }

        arr = np.asarray(self._returns_history, dtype=float)
        avg_return = float(np.mean(arr))
        volatility = float(np.std(arr, ddof=1))

        percentile_5 = float(np.percentile(arr, 5))
        percentile_1 = float(np.percentile(arr, 1))
        var_95 = percentile_5
        var_99 = percentile_1

        lower_tail_95 = arr[arr <= percentile_5]
        lower_tail_99 = arr[arr <= percentile_1]
        cvar_95 = float(lower_tail_95.mean()) if lower_tail_95.size else var_95
        cvar_99 = float(lower_tail_99.mean()) if lower_tail_99.size else var_99

        cumulative = np.cumprod(1 + arr)
        peaks = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - peaks) / peaks
        current_dd = float(drawdowns[-1])
        max_dd = float(drawdowns.min())

        downside_dev = calculate_downside_deviation(arr)
        omega_ratio = calculate_omega_ratio(arr)
        eps = 1e-12
        sharpe = (avg_return / (volatility + eps)) * np.sqrt(252)
        sortino = (avg_return / (downside_dev + eps)) * np.sqrt(252)
        calmar = avg_return / (abs(max_dd) + eps)

        metrics = {
            "volatility": volatility,
            "expected_return": avg_return,
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "cvar_99": cvar_99,
            "current_drawdown": current_dd,
            "max_drawdown": max_dd,
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "calmar_ratio": calmar,
            "downside_deviation": downside_dev,
            "omega_ratio": omega_ratio,
            "observation_count": float(arr.size),
        }

        # Horizon-specific VaR/CVaR
        for label, horizon in self._horizon_windows.items():
            var_h, cvar_h = calculate_parametric_var_cvar(arr, 0.95, horizon)
            metrics[f"var_95_h{label}"] = var_h
            metrics[f"cvar_95_h{label}"] = cvar_h

        scenarios = generate_stress_scenarios(arr)
        stress_losses = {
            f"stress_{name}": float(value)
            for name, value in scenarios.items()
        }
        metrics.update(stress_losses)

        es = calculate_expected_shortfall(arr, horizons=self._horizon_windows.values())
        for label, horizon in self._horizon_windows.items():
            key = f"es_95_h{horizon}"
            if key in es:
                metrics[f"es_95_h{label}"] = es[key]

        # Normalise non-finite values
        for name, value in list(metrics.items()):
            if isinstance(value, float) and not math.isfinite(value):
                metrics[name] = 0.0
        return metrics

    def _concentration_metrics(self, positions: Dict[str, float]) -> Dict[str, float]:
        weights = np.asarray([abs(float(weight)) for weight in positions.values() if weight is not None]) if np else None
        if weights is None or weights.size == 0:
            return {
                "herfindahl_index": 0.0,
                "effective_num_positions": 0.0,
                "largest_position": 0.0,
            }
        normalised = weights / weights.sum() if weights.sum() else weights
        herfindahl = float(np.sum(normalised ** 2))
        return {
            "herfindahl_index": herfindahl,
            "effective_num_positions": float(1.0 / herfindahl) if herfindahl else 0.0,
            "largest_position": float(normalised.max()),
        }

    def scenario_analysis(
        self,
        portfolio_value: float,
        leverage: float = 1.0,
        custom_shocks: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """Generate scenario outcomes based on stored distribution."""
        metrics = self.risk_metrics(leverage=leverage, portfolio_value=portfolio_value)
        base_value = metrics.get("portfolio_value", portfolio_value)
        shocks = custom_shocks or {
            "vol_spike": metrics.get("stress_vol_spike", -0.05),
            "market_crash": metrics.get("stress_market_crash", -0.1),
            "correlation_break": metrics.get("stress_correlation_break", -0.07),
        }
        scenarios: Dict[str, Dict[str, float]] = {}
        for name, shock in shocks.items():
            pnl = base_value * shock
            scenarios[name] = {
                "shock": shock,
                "pnl": pnl,
                "new_value": base_value + pnl,
            }
        return scenarios

    @property
    def metrics_history(self) -> List[Dict[str, float]]:
        return list(self._metrics_history)

    def _store_metrics(self, metrics: Dict[str, float]) -> None:
        snapshot = metrics.copy()
        snapshot["timestamp"] = datetime.now(timezone.utc).isoformat()
        self._metrics_history.append(snapshot)

