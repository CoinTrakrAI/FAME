"""Trading skill adapter plugin for the brain orchestrator."""

from __future__ import annotations

import asyncio
import logging
import re
import os

from typing import Any, Dict, List, Optional

from fame_core.plugin_registry import register_skill_instance
from fame_core.session_manager import SessionManager
from monitoring.trading_metrics_exporter import TradingTelemetryExporter, create_trading_exporter
from services.trading_preferences_manager_enterprise import TradingPreferencesManagerEnterprise
from skills.trading_confirm import TradingConfirmationSkill
from skills.trading_preferences_skill import TradingPreferencesSkill
from skills.trading_skill import TradingSkill


logger = logging.getLogger(__name__)

_preferences_manager = TradingPreferencesManagerEnterprise()
_trading_skill = TradingSkill(preferences_manager=_preferences_manager)
_preferences_skill = TradingPreferencesSkill()
_preferences_skill.manager = _preferences_manager
_confirmation_skill = TradingConfirmationSkill()
_initialized = False
_trading_metrics_exporter: TradingTelemetryExporter | None = None


async def _ensure_initialized() -> None:
    global _initialized
    if not _initialized:
        await _trading_skill.initialize()
        await _preferences_skill.initialize()
        brain = getattr(_trading_skill, "brain", None)
        if brain and getattr(brain, "session_manager", None):
            _preferences_manager.session_manager = brain.session_manager  # type: ignore[attr-defined]
        elif getattr(_preferences_skill, "brain", None) and getattr(_preferences_skill.brain, "session_manager", None):
            _preferences_manager.session_manager = _preferences_skill.brain.session_manager  # type: ignore[attr-defined]
        trading_service = getattr(_trading_skill, "trading_service", None)
        if trading_service:
            try:
                from core.health_monitor import get_health_monitor

                health_monitor = get_health_monitor()
                health_monitor.register_trading_metrics_provider(trading_service.telemetry)
                register_skill_instance("trading_service", trading_service)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Trading telemetry registration failed: %s", exc)

            port = os.getenv("FAME_TRADING_METRICS_PORT")
            if port and port.isdigit():
                try:
                    global _trading_metrics_exporter
                    exporter = create_trading_exporter(trading_service.telemetry)
                    exporter.start_http_server(port=int(port))
                    _trading_metrics_exporter = exporter
                    logger.info("Trading metrics exporter running on port %s", port)
                except Exception as exc:  # pragma: no cover
                    logger.error("Failed to start trading metrics exporter: %s", exc)
        register_skill_instance("trading_skill", _trading_skill)
        _initialized = True


def _extract_symbol(text: str) -> str | None:
    candidates = re.findall(r"\b[A-Z]{1,5}\b", text.upper())
    if candidates:
        return candidates[0]
    return None


async def handle(query: Dict) -> Dict:
    await _ensure_initialized()

    text = (query.get("text") or "").strip()
    if not text:
        return {"error": True, "response": "No trading request provided."}

    session_id = query.get("session_id") or query.get("user") or "default"
    context = {"session_id": session_id}
    lowered = text.lower()
    pref_response = await _maybe_handle_preferences(lowered, text, context)
    if pref_response is not None:
        return pref_response

    # Confirmation flow
    if lowered in {"confirm", "confirm trade", "yes confirm", "execute", "do it"}:
        result = await _confirmation_skill.handle("trading.confirm", {}, context)
        return _format_result(result)
    if lowered in {"cancel", "cancel trade", "no", "stop"}:
        result = await _confirmation_skill.handle("trading.cancel", {}, context)
        return _format_result(result)

    entities: Dict[str, str] = {}
    symbol = _extract_symbol(text)
    if symbol:
        entities["symbol"] = symbol

    if any(keyword in lowered for keyword in ["portfolio", "holdings", "positions"]):
        result = await _trading_skill.handle("trading.portfolio_status", entities, context)
        return _format_result(result)

    if any(keyword in lowered for keyword in ["analyze", "analysis", "research"]):
        result = await _trading_skill.handle("trading.analyze_stock", entities, context)
        return _format_result(result)

    if any(keyword in lowered for keyword in ["signal", "recommendation", "indicator"]):
        result = await _trading_skill.handle("trading.get_signal", entities, context)
        return _format_result(result)

    if "buy" in lowered:
        entities["action"] = "buy"
        result = await _trading_skill.handle("trading.execute_trade", entities, context)
        return _format_result(result)

    if "sell" in lowered:
        entities["action"] = "sell"
        result = await _trading_skill.handle("trading.execute_trade", entities, context)
        return _format_result(result)

    # Default to signal lookup
    result = await _trading_skill.handle("trading.get_signal", entities, context)
    return _format_result(result)


def _format_result(result: Dict) -> Dict:
    response_text = result.get("text") or result.get("response") or "I could not generate a trading response."
    payload = {
        "response": response_text,
        "source": "trading_skill",
        "type": "trading",
        "data": result.get("data"),
    }
    if "confidence" in result:
        payload["confidence"] = result["confidence"]
    if result.get("error"):
        payload["error"] = True
    if result.get("requires_confirmation"):
        payload["requires_confirmation"] = True
    return payload


__all__ = ["handle"]


async def _maybe_handle_preferences(lowered: str, text: str, context: Dict) -> Optional[Dict]:
    intents: List[Dict[str, Any]] = []
    session_id = context.get("session_id", "default")
    for level in ["conservative", "moderate", "aggressive", "extreme"]:
        if level in lowered and "risk tolerance" in lowered:
            intents.append(
                {
                    "intent": "trading.set_risk_tolerance",
                    "entities": {"risk_level": level},
                }
            )
            break
    for style in ["day trading", "swing trading", "position trading", "scalping"]:
        if style in lowered:
            intents.append(
                {
                    "intent": "trading.set_trading_style",
                    "entities": {"trading_style": style.replace(" ", "_")},
                }
            )
            break
    if "watchlist" in lowered:
        symbol = _extract_symbol(text)
        if symbol:
            if "remove" in lowered or "delete" in lowered:
                intents.append({"intent": "trading.remove_from_watchlist", "entities": {"symbol": symbol}})
            elif "add" in lowered or "include" in lowered:
                intents.append({"intent": "trading.add_to_watchlist", "entities": {"symbol": symbol}})
    if "autonomous trading" in lowered:
        if "enable" in lowered or "turn on" in lowered:
            intents.append({"intent": "trading.enable_autonomous", "entities": {}})
        elif "disable" in lowered or "turn off" in lowered:
            intents.append({"intent": "trading.disable_autonomous", "entities": {}})
    asset_classes = [
        cls
        for cls in ["stocks", "crypto", "forex", "options", "futures", "etfs"]
        if cls in lowered
    ]
    if asset_classes and ("only trade" in lowered or "i want to trade" in lowered):
        intents.append({"intent": "trading.set_asset_classes", "entities": {"asset_classes": asset_classes}})
    if not intents:
        return None
    for definition in intents:
        result = await _preferences_skill.handle(definition["intent"], definition["entities"], context)
        if not result.get("error"):
            return _format_result(result)
    last = intents[-1]
    result = await _preferences_skill.handle(last["intent"], last["entities"], context)
    return _format_result(result)


