import asyncio
from datetime import timedelta

import pytest

from services.trading_preferences_manager_enterprise import RateLimitExceeded, TradingPreferencesManagerEnterprise


class FakeSessionManager:
    def __init__(self) -> None:
        self.sessions = {}

    async def get_session(self, session_id: str):
        return self.sessions.get(session_id)

    async def update_session(self, session_id: str, data):
        session = self.sessions.setdefault(session_id, {})
        session.update(data)


def test_manager_returns_default_preferences():
    manager = TradingPreferencesManagerEnterprise(session_manager=FakeSessionManager())

    async def scenario():
        prefs = await manager.get_preferences("session-1", "user-1")
        assert prefs.user_id == "user-1"
        assert prefs.risk_tolerance.value == "moderate"

    asyncio.run(scenario())

def test_manager_updates_preferences_with_audit():
    session_manager = FakeSessionManager()
    manager = TradingPreferencesManagerEnterprise(session_manager=session_manager)

    async def scenario():
        prefs = await manager.update_preferences(
            user_id="user-1",
            session_id="session-1",
            updates={"trading_style": "day_trading"},
            reason="unit_test",
            actor="tester",
        )

        assert prefs.trading_style.value == "day_trading"
        stored = await session_manager.get_session("session-1")
        assert stored["trading_preferences"]["trading_style"] == "day_trading"

    asyncio.run(scenario())


def test_manager_rate_limiting():
    manager = TradingPreferencesManagerEnterprise(session_manager=FakeSessionManager(), write_rate_limit=1)

    async def scenario():
        await manager.update_preferences(
            user_id="user-1",
            session_id="session-1",
            updates={"trading_style": "day_trading"},
            reason="unit_test",
            actor="tester",
        )

        with pytest.raises(RateLimitExceeded):
            await manager.update_preferences(
                user_id="user-1",
                session_id="session-1",
                updates={"trading_style": "position_trading"},
                reason="unit_test",
                actor="tester",
            )

        manager._rate_limit["user-1:write"]["window_start"] -= timedelta(minutes=2)
        prefs = await manager.update_preferences(
            user_id="user-1",
            session_id="session-1",
            updates={"trading_style": "position_trading"},
            reason="unit_test",
            actor="tester",
        )
        assert prefs.trading_style.value == "position_trading"

    asyncio.run(scenario())

