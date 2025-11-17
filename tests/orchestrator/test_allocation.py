from orchestrator.allocation import apply_position_scales, risk_parity_allocation


def test_risk_parity_allocation_balances_inverse_vol():
    assets = ["AAPL", "MSFT", "GOOGL"]
    vol = {"AAPL": 0.2, "MSFT": 0.4, "GOOGL": 0.1}
    weights = risk_parity_allocation(assets, vol)
    assert weights
    assert abs(sum(weights.values()) - 1.0) < 1e-9
    assert weights["GOOGL"] > weights["AAPL"] > weights["MSFT"]


def test_apply_position_scales_limits_risk_and_leverage():
    positions = {"AAPL": 0.3, "MSFT": 0.4, "GOOGL": 0.5}
    scaled = apply_position_scales(positions, target_var=0.05, current_var=0.1, max_leverage=0.8)
    assert scaled
    total_abs = sum(abs(v) for v in scaled.values())
    assert total_abs <= 0.8 + 1e-9

