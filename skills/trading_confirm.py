"""Trade confirmation skill for voice safety."""

from __future__ import annotations

from typing import Dict

from fame_core.skills.base import Skill
from fame_core.session_manager import SessionManager
from services.trading_service import get_trading_service, TradingService


PENDING_TRADE_KEY = "pending_trade"


class TradingConfirmationSkill(Skill):
    def __init__(self) -> None:
        super().__init__()
        self.intents = ["trading.confirm", "trading.cancel"]

    def store_pending_trade(self, session_id: str, trade_data: Dict) -> None:
        SessionManager.set_context(session_id, PENDING_TRADE_KEY, trade_data)

    async def handle(self, intent: str, entities: Dict, context: Dict) -> Dict:
        session_id = context.get("session_id", "default")
        if intent == "trading.confirm":
            return await self._handle_confirmation(session_id)
        if intent == "trading.cancel":
            return self._handle_cancellation(session_id)
        return {"text": "Unsupported trading confirmation intent", "error": True}

    async def _handle_confirmation(self, session_id: str) -> Dict:
        pending = SessionManager.get_context(session_id, PENDING_TRADE_KEY)
        if not pending:
            return {
                "text": "I do not have a trade waiting for confirmation.",
                "error": True,
            }
        service = await get_trading_service()
        result = await service.execute_trade(pending)
        record_method = getattr(service, "record_projected_trade", None)
        if callable(record_method):
            try:
                record_method(pending)
            except Exception as exc:  # pragma: no cover - defensive
                logger = getattr(service, "logger", None)
                if logger:
                    logger.debug("Failed to record projected trade: %s", exc)
        SessionManager.clear_context(session_id, PENDING_TRADE_KEY)
        return {
            "text": result.get("message", "Trade completed."),
            "data": result,
            "clear_context": True,
        }

    def _handle_cancellation(self, session_id: str) -> Dict:
        SessionManager.clear_context(session_id, PENDING_TRADE_KEY)
        return {
            "text": "Trade cancelled. I won't execute that order.",
            "clear_context": True,
        }


__all__ = ["TradingConfirmationSkill", "PENDING_TRADE_KEY"]


