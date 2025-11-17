"""Enterprise-grade trading preferences manager with resilience and telemetry."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

try:
    from circuitbreaker import circuit
except ImportError:  # pragma: no cover - fallback
    def circuit(*args, **kwargs):  # type: ignore
        def decorator(func):
            async def wrapper(*f_args, **f_kwargs):
                return await func(*f_args, **f_kwargs)

            return wrapper

        return decorator

from monitoring.trading_preferences_metrics import (
    PREFERENCE_CACHE_HIT_RATIO,
    PREFERENCE_ERROR_COUNTER,
    PREFERENCE_OPERATION_LATENCY,
    PREFERENCE_UPDATE_COUNTER,
)
from models.trading_preferences_enterprise import (
    RiskTolerance,
    TradingPreferencesEnterprise,
)
from services.cache.enterprise_cache import EnterpriseCache

logger = logging.getLogger(__name__)


class TradingPreferencesManagerEnterprise:
    """Main access point for trading preferences with caching, rate limits, and circuit breakers."""

    def __init__(
        self,
        session_manager: Optional[Any] = None,
        redis_client: Optional[Any] = None,
        cache: Optional[EnterpriseCache] = None,
        read_rate_limit: int = 100,
        write_rate_limit: int = 10,
    ) -> None:
        self.session_manager = session_manager
        self.redis_client = redis_client
        self.cache = cache or EnterpriseCache()
        self.read_rate_limit = read_rate_limit
        self.write_rate_limit = write_rate_limit
        self._rate_limit: Dict[str, Dict[str, Any]] = {}

    @PREFERENCE_OPERATION_LATENCY.time()
    @circuit(failure_threshold=3, expected_exception=Exception, recovery_timeout=30)
    async def get_preferences(self, session_id: str, user_id: str) -> TradingPreferencesEnterprise:
        cache_key = self._cache_key(session_id, user_id)
        try:
            cached = await self.cache.get(cache_key)
            if cached:
                stats = self.cache.get_stats()
                PREFERENCE_CACHE_HIT_RATIO.set(stats.get("hit_ratio", 0))
                return TradingPreferencesEnterprise.model_validate(cached)
            self._throttle(user_id, "read")
            data = await self._load_preferences(session_id, user_id)
            if data is None:
                data = self._create_default_preferences(user_id, session_id).model_dump()
            prefs = TradingPreferencesEnterprise.model_validate(data)
            await self.cache.set(cache_key, prefs.model_dump())
            return prefs
        except Exception as exc:
            PREFERENCE_ERROR_COUNTER.labels(error_type=type(exc).__name__).inc()
            logger.error(
                "Failed to load trading preferences",
                extra={"user_id": user_id, "session_id": session_id, "error": str(exc)},
            )
            raise

    @circuit(failure_threshold=2, expected_exception=Exception, recovery_timeout=60)
    async def update_preferences(
        self,
        user_id: str,
        session_id: str,
        updates: Dict[str, Any],
        reason: str,
        actor: str,
    ) -> TradingPreferencesEnterprise:
        self._throttle(user_id, "write")
        try:
            preferences = await self.get_preferences(session_id, user_id)
            preferences.update_preferences(updates, reason=reason, actor=actor)
            await self._validate_business_rules(preferences)
            await self._persist_preferences(preferences, user_id)
            await self.cache.set(self._cache_key(session_id, user_id), preferences.model_dump())
            PREFERENCE_UPDATE_COUNTER.labels(risk_level=preferences.risk_tolerance.value).inc()
            logger.info(
                "Trading preferences updated",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "actor": actor,
                    "changes": list(updates.keys()),
                },
            )
            return preferences
        except Exception as exc:
            PREFERENCE_ERROR_COUNTER.labels(error_type=type(exc).__name__).inc()
            logger.error(
                "Failed to update trading preferences",
                extra={
                    "user_id": user_id,
                    "session_id": session_id,
                    "actor": actor,
                    "error": str(exc),
                },
            )
            raise

    async def validate_trade(
        self,
        session_id: str,
        user_id: str,
        symbol: str,
        position_size: float,
        portfolio_value: float,
    ) -> Dict[str, Any]:
        preferences = await self.get_preferences(session_id, user_id)
        status = {"allowed": True, "reasons": [], "adjusted_size": position_size}
        if symbol.upper() in {item.upper() for item in preferences.banned_symbols}:
            status["allowed"] = False
            status["reasons"].append(f"{symbol.upper()} is on your restricted list.")
        max_size = portfolio_value * preferences.risk_parameters.max_position_size_pct
        if position_size > max_size:
            status["adjusted_size"] = max_size
            status["reasons"].append("Position reduced to respect your risk parameters.")
        return status

    async def _load_preferences(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            if self.redis_client:
                result = await self.redis_client.get(self._redis_key(user_id))
                if result:
                    return result if isinstance(result, dict) else self._deserialize(result)
            if self.session_manager:
                if hasattr(self.session_manager, "get_session"):
                    session = await self.session_manager.get_session(session_id)
                    return session.get("trading_preferences") if session else None
                stored = self.session_manager.get_context(session_id, "trading_preferences")  # type: ignore[attr-defined]
                return stored
        except Exception as exc:
            raise ServiceUnavailable(f"Unable to load preferences: {exc}") from exc
        return None

    async def _persist_preferences(
        self,
        preferences: TradingPreferencesEnterprise,
        user_id: str,
    ) -> None:
        last_exc: Optional[Exception] = None
        for attempt in range(3):
            try:
                if self.redis_client:
                    await self.redis_client.set(
                        self._redis_key(user_id),
                        self._serialize(preferences.model_dump()),
                        ex=86400,
                    )
                elif self.session_manager:
                    if hasattr(self.session_manager, "update_session"):
                        await self.session_manager.update_session(
                            preferences.session_id,
                            {"trading_preferences": preferences.model_dump()},
                        )
                    else:
                        self.session_manager.set_context(  # type: ignore[attr-defined]
                            preferences.session_id,
                            "trading_preferences",
                            preferences.model_dump(),
                        )
                return
            except Exception as exc:
                last_exc = exc
                await asyncio.sleep(2**attempt)
        raise PersistenceError(f"Failed to persist preferences: {last_exc}") from last_exc

    async def _validate_business_rules(self, preferences: TradingPreferencesEnterprise) -> None:
        if (
            preferences.risk_tolerance == RiskTolerance.CONSERVATIVE
            and preferences.risk_parameters.max_position_size_pct > 0.05
        ):
            raise BusinessRuleViolation("Conservative risk tolerance limited to 5% position size.")

    def _throttle(self, user_id: str, operation: str) -> None:
        now = datetime.now(timezone.utc)
        key = f"{user_id}:{operation}"
        bucket = self._rate_limit.setdefault(
            key, {"count": 0, "window_start": now, "limit": self._limit_for_operation(operation)}
        )
        if now - bucket["window_start"] > timedelta(minutes=1):
            bucket["count"] = 0
            bucket["window_start"] = now
        if bucket["count"] >= bucket["limit"]:
            raise RateLimitExceeded(f"Rate limit exceeded for {operation}")
        bucket["count"] += 1

    def _limit_for_operation(self, operation: str) -> int:
        return self.read_rate_limit if operation == "read" else self.write_rate_limit

    def _cache_key(self, session_id: str, user_id: str) -> str:
        return f"prefs:{user_id}:{session_id}"

    def _redis_key(self, user_id: str) -> str:
        return f"trading_preferences:{user_id}"

    def _serialize(self, data: Dict[str, Any]) -> Any:
        return data

    def _deserialize(self, payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return payload
        raise ValueError("Unsupported serialization format for trading preferences.")

    def _create_default_preferences(self, user_id: str, session_id: str) -> TradingPreferencesEnterprise:
        return TradingPreferencesEnterprise(
            user_id=user_id,
            session_id=session_id,
            risk_tolerance=RiskTolerance.MODERATE,
            trading_style="swing_trading",
            risk_parameters=self._default_risk_parameters(),
        )

    def _default_risk_parameters(self) -> Dict[str, Any]:
        return {
            "max_position_size_pct": 0.05,
            "max_daily_loss_pct": 0.02,
            "max_drawdown_pct": 0.12,
            "min_risk_reward_ratio": 1.5,
            "stop_loss_pct": 0.02,
        }


class RateLimitExceeded(Exception):
    """Thrown when a caller exceeds the configured rate limit."""


class BusinessRuleViolation(Exception):
    """Raised when a preference change violates compliance or business rules."""


class ServiceUnavailable(Exception):
    """Raised when downstream storage is unavailable."""


class PersistenceError(Exception):
    """Raised when preferences could not be persisted after retries."""


