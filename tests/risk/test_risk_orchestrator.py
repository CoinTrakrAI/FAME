from risk import RiskConstraints, RiskOrchestrator


def test_risk_orchestrator_scales_positions():
    orchestrator = RiskOrchestrator(RiskConstraints(max_position=0.1, max_leverage=0.3))
    signals = {"A": 0.5, "B": 0.2}
    adjusted = orchestrator.apply(signals)
    for size in adjusted.values():
        assert abs(size) <= 0.1 + 1e-9
    assert sum(abs(size) for size in adjusted.values()) <= 0.3 + 1e-9


def test_risk_orchestrator_records_returns():
    orchestrator = RiskOrchestrator()
    returns = [0.01, -0.015, 0.02, -0.005, 0.004]
    orchestrator.extend_returns(returns)
    metrics = orchestrator.risk_metrics()
    assert "var_95" in metrics
    assert "cvar_95" in metrics
    assert "sharpe_ratio" in metrics
    assert metrics["volatility"] >= 0.0
    assert metrics["max_drawdown"] <= 0.0


def test_risk_metrics_with_positions_and_leverage():
    orchestrator = RiskOrchestrator()
    orchestrator.extend_returns([0.01, -0.02, 0.015, -0.01, 0.005])
    positions = {"AAPL": 0.4, "MSFT": 0.35, "GOOGL": 0.25}
    metrics = orchestrator.risk_metrics(leverage=1.5, positions=positions, portfolio_value=100000)
    assert metrics["herfindahl_index"] > 0
    assert metrics["effective_num_positions"] >= 1
    assert metrics["largest_position"] <= 1
    assert metrics["var_95"] != 0
    assert metrics["portfolio_value"] == 100000
    assert "var_95_h1d" in metrics
    assert "cvar_95_h5d" in metrics
    assert "es_95_h1d" in metrics
    assert "turnover_ratio" in metrics


def test_scenario_analysis():
    orchestrator = RiskOrchestrator()
    orchestrator.extend_returns([0.02, -0.03, 0.015, -0.005, 0.01])
    scenarios = orchestrator.scenario_analysis(portfolio_value=200000)
    assert "vol_spike" in scenarios
    assert "market_crash" in scenarios
    for scenario in scenarios.values():
        assert "shock" in scenario
        assert "pnl" in scenario
        assert "new_value" in scenario

