"""Trading skill entry point registered via the plugin registry."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from fame_core.plugin_registry import register_skill
from fame_core.session_manager import SessionManager
from fame_core.skills.base import Skill
from config.trading_config import get_trading_config
from services.trading_service import TradingConfig, get_trading_service
from skills.trading_confirm import PENDING_TRADE_KEY, TradingConfirmationSkill


@register_skill("trading")
class TradingSkill(Skill):
    def __init__(self, preferences_manager=None) -> None:
        super().__init__()
        self.name = "trading"
        self.description = "Stock analysis, signals, and trade execution support"
        self.intents = [
            "trading.get_signal",
            "trading.execute_trade",
            "trading.portfolio_status",
            "trading.analyze_stock",
        ]
        self.trading_service = None
        self.preferences_manager = preferences_manager
        self.confirmation_skill = TradingConfirmationSkill()

    async def initialize(self):
        if self.trading_service is None:
            config = get_trading_config()
            self.trading_service = await get_trading_service(
                config,
                preferences_manager=self.preferences_manager,
            )
        return self

    async def handle(self, intent: str, entities: Dict, context: Dict) -> Dict:
        if self.trading_service is None:
            await self.initialize()

            return await self._handle_get_signal(entities, context)
        if intent == "trading.execute_trade":
            return await self._handle_execute_trade(entities, context)
        if intent == "trading.portfolio_status":
            return await self.trading_service.portfolio_snapshot()
        if intent == "trading.analyze_stock":
            return await self._handle_analyze_stock(entities, context)
        return {"text": "I am not sure how to handle that trading request.", "error": True}

    async def _handle_get_signal(self, entities: Dict, context: Dict) -> Dict:
        symbol = entities.get("symbol", "").upper()
        if not symbol:
            return {"text": "Please provide a stock symbol.", "error": True}
        session_id = context.get("session_id", "default")
        user_id = self._get_user_id(context, session_id)
        result = await self.trading_service.get_personalized_signals(symbol, session_id, user_id)
        signals = result.get("signals", [])
        if not signals:
            return {
                "text": f"I do not have a strong signal for {symbol} at the moment.",
                "data": result,
            }
        best = max(signals, key=lambda entry: entry.get("confidence", 0.0))
        text = (
            f"Best signal for {symbol}: {best['signal_type']} with {best['confidence']:.0%} confidence. "
            f"Entry {best['entry_price']}, stop {best['stop_loss']}, take profit {best['take_profit']}."
        )
        return {"text": text, "data": result}

    async def _handle_execute_trade(self, entities: Dict, context: Dict) -> Dict:
        symbol = entities.get("symbol", "").upper()
        action = entities.get("action", "signal")
        session_id = context.get("session_id", "default")
        if not symbol:
            return {"text": "Please specify which symbol you would like to trade.", "error": True}

        # Gather signal for confirmation context
        user_id = self._get_user_id(context, session_id)
        signal_data = await self.trading_service.get_personalized_signals(symbol, session_id, user_id)
        signals = signal_data.get("signals", [])
        best_signal = max(signals, key=lambda entry: entry.get("confidence", 0.0)) if signals else None
        trade_data = {
            "symbol": symbol,
            "action": action,
            "requested_at": datetime.now().isoformat(),
            "signal_snapshot": signal_data,
            "best_signal": best_signal,
            "session_id": session_id,
        }
        self.confirmation_skill.store_pending_trade(session_id, trade_data)
        SessionManager.set_context(session_id, PENDING_TRADE_KEY, trade_data)

        if best_signal:
            confirmation_text = (
                f"Confirm {action.upper()} order for {symbol}? Signal {best_signal['signal_type']} "
                f"with {best_signal['confidence']:.0%} confidence at {best_signal['entry_price']}. "
                "Say 'confirm' or 'cancel'."
            )
        else:
            confirmation_text = (
                f"I can place a {action.upper()} order for {symbol}, but I do not see a strong signal. "
                "Say 'confirm' to proceed or 'cancel' to abort."
            )

        return {
            "text": confirmation_text,
            "data": trade_data,
            "requires_confirmation": True,
        }

    async def _handle_analyze_stock(self, entities: Dict, context: Dict) -> Dict:
        symbol = entities.get("symbol", "").upper()
        if not symbol:
            return {"text": "Which symbol would you like me to analyze?", "error": True}
        session_id = context.get("session_id", "default")
        user_id = self._get_user_id(context, session_id)
        result = await self.trading_service.get_personalized_signals(symbol, session_id, user_id)
        signals = result.get("signals", [])
        if signals:
            summary = " | ".join(
                f"{entry['strategy']}: {entry['signal_type']} ({entry['confidence']:.0%})" for entry in signals
            )
            text = f"Analysis for {symbol}: {summary}"
        else:
            text = f"I do not have a clear trading signal for {symbol} right now."
        return {"text": text, "data": result}

    def _get_user_id(self, context: Dict, fallback: str) -> str:
        user_id = context.get("user_id") or context.get("user") or context.get("account")
        if isinstance(user_id, str) and user_id.strip():
            return user_id.strip()
        return fallback


__all__ = ["TradingSkill"]


