import numpy as np

from risk.advanced_metrics import (
    calculate_downside_deviation,
    calculate_expected_shortfall,
    calculate_liquidity_metrics,
    calculate_omega_ratio,
    calculate_parametric_var_cvar,
    generate_stress_scenarios,
)


def test_parametric_var_cvar_scales_with_horizon():
    returns = np.array([0.01, -0.02, 0.015, -0.012, 0.007])
    var_1, cvar_1 = calculate_parametric_var_cvar(returns, 0.95, 1)
    var_5, cvar_5 = calculate_parametric_var_cvar(returns, 0.95, 5)
    assert var_1 <= 0
    assert cvar_1 <= var_1
    assert var_5 <= 0
    assert cvar_5 <= var_5


def test_expected_shortfall_produces_horizon_keys():
    returns = np.array([0.01, -0.02, 0.015, -0.012, 0.007])
    es = calculate_expected_shortfall(returns, horizons=(1, 5))
    assert "es_95_h1" in es
    assert "es_95_h5" in es
    assert es["es_95_h5"] <= 0


def test_downside_deviation_zero_when_no_losses():
    returns = np.array([0.01, 0.02, 0.03])
    assert calculate_downside_deviation(returns) == 0.0


def test_omega_ratio_handles_losses():
    returns = np.array([0.01, -0.02, 0.015, -0.012, 0.007])
    omega = calculate_omega_ratio(returns)
    assert omega >= 0


def test_generate_stress_scenarios_defaults():
    scenarios = generate_stress_scenarios(np.array([]))
    assert "vol_spike" in scenarios
    assert scenarios["market_crash"] < 0


def test_liquidity_metrics_for_weights():
    positions = {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
    metrics = calculate_liquidity_metrics(positions, portfolio_value=100000)
    assert metrics["turnover_ratio"] > 0
    assert metrics["liquidity_pressure"] > 0

