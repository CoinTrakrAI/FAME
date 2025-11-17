from datetime import datetime, timedelta, timezone

import pytest

from models.trading_preferences_enterprise import (
    RiskTolerance,
    TradingPreferencesEnterprise,
    TradingStyle,
)


def create_base_preferences() -> TradingPreferencesEnterprise:
    return TradingPreferencesEnterprise(
        user_id="user-123",
        session_id="session-abc",
        risk_tolerance=RiskTolerance.MODERATE,
        trading_style="swing_trading",
        risk_parameters={
            "max_position_size_pct": 0.05,
            "max_daily_loss_pct": 0.02,
            "max_drawdown_pct": 0.12,
            "min_risk_reward_ratio": 1.5,
            "stop_loss_pct": 0.02,
        },
    )


def test_audit_trail_captures_updates():
    prefs = create_base_preferences()
    prefs.update_preferences({"trading_style": "day_trading"}, reason="unit_test", actor="tester")

    assert prefs.trading_style.value == "day_trading"
    assert len(prefs.audit_trail) == 1
    assert prefs.audit_trail[0].changes["trading_style"] == TradingStyle.DAY_TRADING


def test_risk_tolerance_cooldown_enforced(monkeypatch):
    prefs = create_base_preferences()
    prefs.update_preferences({"risk_tolerance": "aggressive"}, reason="unit_test", actor="tester")

    # simulate audit entry being very recent
    recent_entry = prefs.audit_trail[-1]
    recent_entry.timestamp = datetime.now(timezone.utc) - timedelta(hours=1)

    with pytest.raises(ValueError):
        prefs.update_preferences({"risk_tolerance": "extreme"}, reason="unit_test", actor="tester")


def test_autonomous_trading_validation():
    prefs = create_base_preferences()

    with pytest.raises(ValueError):
        prefs.update_preferences({"allow_autonomous_trading": True}, reason="unit_test", actor="tester")

    prefs.update_preferences(
        {
            "compliance_acknowledged": True,
            "risk_disclosure_accepted": True,
            "allow_autonomous_trading": True,
            "max_autonomous_position_size": 0.05,
        },
        reason="unit_test",
        actor="tester",
    )

    assert prefs.allow_autonomous_trading is True
    assert prefs.max_autonomous_position_size == 0.05

