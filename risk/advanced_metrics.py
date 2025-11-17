"""
Advanced risk analytics helpers.
"""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

try:  # optional dependency
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore


def _aggregate_returns(returns: "np.ndarray", horizon: int) -> "np.ndarray":
    if returns.size == 0 or horizon <= 1:
        return returns
    if returns.size < horizon:
        # compound available series
        compounded = (np.prod(1 + returns) - 1.0).reshape(1)
        return compounded
    window = []
    for idx in range(returns.size - horizon + 1):
        window_slice = returns[idx : idx + horizon]
        compounded = float(np.prod(1 + window_slice) - 1.0)
        window.append(compounded)
    return np.asarray(window, dtype=float)


def calculate_parametric_var_cvar(
    returns: "np.ndarray", confidence: float, horizon: int
) -> Tuple[float, float]:
    if np is None or returns.size == 0:
        return 0.0, 0.0
    aggregated = _aggregate_returns(returns, max(1, horizon))
    if aggregated.size == 0:
        aggregated = returns
    var = float(np.quantile(aggregated, 1 - confidence))
    tail = aggregated[aggregated <= var]
    cvar = float(tail.mean()) if tail.size else var
    return var, cvar


def calculate_expected_shortfall(
    returns: "np.ndarray", horizons: Iterable[int] = (1, 5, 21), confidence: float = 0.95
) -> Dict[str, float]:
    label = int(confidence * 100)
    if np is None or returns.size == 0:
        return {f"es_{label}_h{h}": 0.0 for h in horizons}
    results: Dict[str, float] = {}
    for horizon in horizons:
        _, cvar = calculate_parametric_var_cvar(returns, confidence, max(1, horizon))
        results[f"es_{label}_h{horizon}"] = cvar
    return results


def calculate_downside_deviation(returns: "np.ndarray") -> float:
    if np is None or returns.size == 0:
        return 0.0
    downside = returns[returns < 0]
    if downside.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(downside**2)))


def calculate_omega_ratio(returns: "np.ndarray", threshold: float = 0.0) -> float:
    if np is None or returns.size == 0:
        return 0.0
    gains = returns[returns > threshold] - threshold
    losses = threshold - returns[returns < threshold]
    total_gains = float(np.sum(gains)) if gains.size else 0.0
    total_losses = float(np.sum(losses)) if losses.size else 0.0
    if total_losses == 0.0:
        return float("inf") if total_gains > 0 else 0.0
    return total_gains / total_losses


def generate_stress_scenarios(returns: "np.ndarray") -> Dict[str, float]:
    if np is None or returns.size == 0:
        return {
            "vol_spike": -0.05,
            "market_crash": -0.1,
            "correlation_break": -0.07,
        }
    sigma = float(np.std(returns, ddof=1))
    crash = float(np.percentile(returns, 1))
    severe = float(np.percentile(returns, 5))
    correlation_break = float(min(-0.05, (crash + severe) / 2))
    return {
        "vol_spike": -abs(sigma * 2.0),
        "market_crash": crash,
        "correlation_break": correlation_break,
    }


def calculate_liquidity_metrics(
    positions: Dict[str, float], portfolio_value: float
) -> Dict[str, float]:
    if portfolio_value <= 0:
        portfolio_value = 1.0
    abs_positions = [abs(float(val)) for val in positions.values()]
    if not abs_positions:
        return {
            "liquidity_pressure": 0.0,
            "turnover_ratio": 0.0,
        }
    gross_exposure = float(sum(abs_positions))
    treat_as_weights = gross_exposure <= 1.5
    if treat_as_weights:
        gross_notional = gross_exposure * portfolio_value
        turnover_ratio = gross_exposure
        liquidity_pressure = float(max(abs_positions))
    else:
        gross_notional = gross_exposure
        turnover_ratio = gross_exposure / max(portfolio_value, 1.0)
        liquidity_pressure = float(max(abs_positions)) / max(portfolio_value, 1.0)
    return {
        "liquidity_pressure": liquidity_pressure,
        "turnover_ratio": turnover_ratio,
        "gross_exposure_notional": gross_notional,
    }

