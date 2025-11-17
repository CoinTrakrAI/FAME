"""Skill for managing trading preferences via conversational commands."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

from fame_core.plugin_registry import register_skill
from fame_core.session_manager import SessionManager
from fame_core.skills.base import Skill
from models.trading_preferences_enterprise import RiskTolerance, TradingStyle
from services.trading_preferences_manager_enterprise import (
    BusinessRuleViolation,
    RateLimitExceeded,
    ServiceUnavailable,
    TradingPreferencesManagerEnterprise,
)

logger = logging.getLogger(__name__)

VALID_RISK_LEVELS = {item.value for item in RiskTolerance}
VALID_TRADING_STYLES = {item.value for item in TradingStyle}
VALID_ASSET_CLASSES = {"stocks", "crypto", "forex", "options", "futures", "etfs"}


@register_skill("trading_preferences")
class TradingPreferencesSkill(Skill):
    """Voice-facing skill to manage enterprise trading preferences."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "trading_preferences"
        self.description = "Manage trading risk settings, watchlists, and automation controls."
        self.intents = [
            "trading.set_risk_tolerance",
            "trading.set_trading_style",
            "trading.add_to_watchlist",
            "trading.remove_from_watchlist",
            "trading.enable_autonomous",
            "trading.disable_autonomous",
            "trading.show_preferences",
            "trading.set_asset_classes",
        ]
        self.manager: Optional[TradingPreferencesManagerEnterprise] = None

    async def initialize(self):
        if self.manager is None:
            session_mgr = getattr(self.brain, "session_manager", None) if hasattr(self, "brain") else None
            self.manager = TradingPreferencesManagerEnterprise(session_manager=session_mgr)
        return self

    async def handle(self, intent: str, entities: Dict, context: Dict) -> Dict:
        manager = self._ensure_manager()
        session_id = context.get("session_id") or "default"
        user_id = self._get_user_id(context, session_id)
        try:
            if intent == "trading.set_risk_tolerance":
                return await self._handle_set_risk(manager, session_id, user_id, entities)
            if intent == "trading.set_trading_style":
                return await self._handle_set_style(manager, session_id, user_id, entities)
            if intent == "trading.add_to_watchlist":
                return await self._handle_watchlist(manager, session_id, user_id, entities, add=True)
            if intent == "trading.remove_from_watchlist":
                return await self._handle_watchlist(manager, session_id, user_id, entities, add=False)
            if intent == "trading.enable_autonomous":
                return await self._handle_autonomy(manager, session_id, user_id, entities, enable=True)
            if intent == "trading.disable_autonomous":
                return await self._handle_autonomy(manager, session_id, user_id, entities, enable=False)
            if intent == "trading.show_preferences":
                return await self._handle_show(manager, session_id, user_id)
            if intent == "trading.set_asset_classes":
                return await self._handle_asset_classes(manager, session_id, user_id, entities)
            return self._error("I did not recognise that preference command.")
        except RateLimitExceeded:
            return self._error("Slow down a little. You are making preferences changes too quickly.")
        except BusinessRuleViolation as exc:
            return self._error(str(exc))
        except ServiceUnavailable:
            return self._error("My preference service is temporarily unavailable. Please try again shortly.")
        except Exception as exc:  # pragma: no cover - defensive guardrail
            logger.exception("Trading preferences skill error: %s", exc)
            return self._error("I ran into a problem updating your preferences.")

    async def _handle_set_risk(
        self,
        manager: TradingPreferencesManagerEnterprise,
        session_id: str,
        user_id: str,
        entities: Dict[str, Any],
    ) -> Dict[str, Any]:
        risk_level = str(entities.get("risk_level", "")).lower()
        if risk_level not in VALID_RISK_LEVELS:
            valid = ", ".join(sorted(VALID_RISK_LEVELS))
            return self._error(f"Please specify a valid risk level: {valid}.")
        prefs = await manager.update_preferences(
            user_id=user_id,
            session_id=session_id,
            updates={"risk_tolerance": risk_level},
            reason="user_request",
            actor=user_id,
        )
        params = prefs.risk_parameters
        return {
            "text": (
                f"Risk tolerance set to {risk_level}. "
                f"Max position size {params.max_position_size_pct:.1%}, "
                f"daily loss {params.max_daily_loss_pct:.1%}, "
                f"stop loss {params.stop_loss_pct:.1%}."
            ),
            "data": {
                "risk_tolerance": prefs.risk_tolerance.value,
                "risk_parameters": params.dict(),
            },
        }

    async def _handle_set_style(
        self,
        manager: TradingPreferencesManagerEnterprise,
        session_id: str,
        user_id: str,
        entities: Dict[str, Any],
    ) -> Dict[str, Any]:
        style = str(entities.get("trading_style", "")).lower().replace(" ", "_")
        if style not in VALID_TRADING_STYLES:
            valid = ", ".join(sorted(VALID_TRADING_STYLES))
            return self._error(f"Please specify a valid trading style: {valid}.")
        prefs = await manager.update_preferences(
            user_id=user_id,
            session_id=session_id,
            updates={"trading_style": style},
            reason="user_request",
            actor=user_id,
        )
        descriptions = {
            "day_trading": "focus on intraday movement and close positions before the market closes.",
            "swing_trading": "hold trades for several days to capture price swings.",
            "position_trading": "hold positions for weeks or months based on macro trends.",
            "scalping": "enter and exit trades within minutes for small price movements.",
        }
        return {
            "text": f"Trading style set to {style.replace('_', ' ')}. You now {descriptions[style]}",
            "data": {"trading_style": prefs.trading_style.value},
        }

    async def _handle_watchlist(
        self,
        manager: TradingPreferencesManagerEnterprise,
        session_id: str,
        user_id: str,
        entities: Dict[str, Any],
        *,
        add: bool,
    ) -> Dict[str, Any]:
        symbol = self._sanitize_symbol(entities.get("symbol"))
        if not symbol:
            action = "add" if add else "remove"
            return self._error(f"Please specify a symbol to {action}.")
        field = "watchlist"
        current = await manager.get_preferences(session_id, user_id)
        watchlist = list({item.upper() for item in current.watchlist})
        if add:
            if symbol in watchlist:
                return {"text": f"{symbol} is already on your watchlist.", "data": {"watchlist": watchlist}}
            watchlist.append(symbol)
        else:
            if symbol not in watchlist:
                return {"text": f"{symbol} was not on your watchlist.", "data": {"watchlist": watchlist}}
            watchlist.remove(symbol)
        prefs = await manager.update_preferences(
            user_id=user_id,
            session_id=session_id,
            updates={field: watchlist},
            reason="user_request",
            actor=user_id,
        )
        verb = "added to" if add else "removed from"
        return {
            "text": f"{symbol} {verb} your watchlist. Monitoring {len(prefs.watchlist)} symbols.",
            "data": {"watchlist": prefs.watchlist},
        }

    async def _handle_autonomy(
        self,
        manager: TradingPreferencesManagerEnterprise,
        session_id: str,
        user_id: str,
        entities: Dict[str, Any],
        *,
        enable: bool,
    ) -> Dict[str, Any]:
        current = await manager.get_preferences(session_id, user_id)
        updates: Dict[str, Any] = {"allow_autonomous_trading": enable}
        if enable:
            max_size = self._safe_float(entities.get("max_position_size"), fallback=current.max_autonomous_position_size)
            updates["max_autonomous_position_size"] = max(0.005, min(0.15, max_size))
        prefs = await manager.update_preferences(
            user_id=user_id,
            session_id=session_id,
            updates=updates,
            reason="user_request",
            actor=user_id,
        )
        SessionManager.set_context(session_id, "trading_autonomous", enable)
        if enable:
            return {
                "text": (
                    f"Autonomous trading enabled with a {prefs.max_autonomous_position_size:.1%} position cap. "
                    "I'll still ask for confirmation when needed."
                ),
                "data": {"autonomous_trading": True, "max_autonomous_position_size": prefs.max_autonomous_position_size},
            }
        return {"text": "Autonomous trading disabled. I will await confirmation for every trade.", "data": {"autonomous_trading": False}}

    async def _handle_show(
        self,
        manager: TradingPreferencesManagerEnterprise,
        session_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        prefs = await manager.get_preferences(session_id, user_id)
        watchlist_preview = ", ".join(prefs.watchlist[:5]) if prefs.watchlist else "none yet"
        text = (
            f"Your profile: risk tolerance {prefs.risk_tolerance.value}, "
            f"trading style {prefs.trading_style.value.replace('_', ' ')}, "
            f"autonomous trading {'enabled' if prefs.allow_autonomous_trading else 'disabled'}, "
            f"watchlist highlights {watchlist_preview}."
        )
        return {"text": text, "data": prefs.dict()}

    async def _handle_asset_classes(
        self,
        manager: TradingPreferencesManagerEnterprise,
        session_id: str,
        user_id: str,
        entities: Dict[str, Any],
    ) -> Dict[str, Any]:
        classes = self._normalize_asset_classes(entities.get("asset_classes"))
        if not classes:
            valid = ", ".join(sorted(VALID_ASSET_CLASSES))
            return self._error(f"Please specify which asset classes you want to trade: {valid}.")
        prefs = await manager.update_preferences(
            user_id=user_id,
            session_id=session_id,
            updates={"enabled_asset_classes": classes},
            reason="user_request",
            actor=user_id,
        )
        return {
            "text": f"Asset classes updated to {', '.join(classes)}.",
            "data": {"enabled_asset_classes": prefs.enabled_asset_classes},
        }

    def _ensure_manager(self) -> TradingPreferencesManagerEnterprise:
        if self.manager is None:
            self.manager = TradingPreferencesManagerEnterprise()
        return self.manager

    def _get_user_id(self, context: Dict[str, Any], fallback: str) -> str:
        user_id = context.get("user_id") or context.get("user") or context.get("account")
        if isinstance(user_id, str) and user_id.strip():
            return user_id.strip()
        return fallback

    def _sanitize_symbol(self, value: Any) -> Optional[str]:
        if isinstance(value, str):
            cleaned = "".join(ch for ch in value.upper() if ch.isalnum() or ch == "-")
            return cleaned if cleaned else None
        return None

    def _normalize_asset_classes(self, values: Any) -> List[str]:
        if not values:
            return []
        if isinstance(values, str):
            candidate = [values]
        elif isinstance(values, Iterable):
            candidate = list(values)
        else:
            return []
        normalised = []
        for item in candidate:
            item_lower = str(item).lower()
            if item_lower in VALID_ASSET_CLASSES:
                normalised.append(item_lower)
        return normalised

    def _safe_float(self, value: Any, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    def _error(self, message: str) -> Dict[str, Any]:
        return {"text": message, "error": True}


__all__ = ["TradingPreferencesSkill"]
