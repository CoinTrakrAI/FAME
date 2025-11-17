"""Resilient trading service module for Stage 3 integration."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
import numpy as np
import pandas as pd
try:
    from circuitbreaker import circuit
except ImportError:  # pragma: no cover - optional dependency
    def circuit(*args, **kwargs):  # type: ignore
        def decorator(func):
            async def wrapper(*f_args, **f_kwargs):
                return await func(*f_args, **f_kwargs)

            return wrapper

        return decorator

    class CircuitBreakerError(Exception):
        pass

    circuit.CircuitBreakerError = CircuitBreakerError  # type: ignore[attr-defined]

from monitoring.tracing import span_async
from services.execution_service import ExecutionService
from services.trading_data import HistoricalDataConfig, HistoricalDataService
from services.technical_indicators import get_technical_engine
from services.trading_preferences_manager_enterprise import TradingPreferencesManagerEnterprise
from models.trading_preferences_enterprise import RiskTolerance, TradingPreferencesEnterprise

try:
    from telemetry.events import emit_training_event
except ImportError:  # pragma: no cover - optional dependency
    emit_training_event = None


logger = logging.getLogger(__name__)


class TradingSignalType(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class TradingSignal:
    symbol: str
    signal_type: TradingSignalType
    strategy: str
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit: float
    rationale: str
    timestamp: datetime


@dataclass
class TradingConfig:
    finnhub_key: str
    serpapi_key: str
    coingecko_key: str
    alpha_vantage_key: str
    initial_capital: float = 100_000.0
    max_drawdown: float = 0.08
    max_daily_loss: float = 0.03


class MarketDataService:
    """Aggregates market data with resilience and caching."""

    def __init__(self, config: TradingConfig) -> None:
        self.config = config
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        self._historical_service = HistoricalDataService(
            HistoricalDataConfig(
                finnhub_key=config.finnhub_key,
                alpha_vantage_key=config.alpha_vantage_key,
            )
        )
        self._technical_engine = get_technical_engine()
        self._cache: Dict[str, tuple[Dict, float]] = {}
        self._cache_ttl_seconds = 120

    async def shutdown(self) -> None:
        await self._client.aclose()
        await self._historical_service.shutdown()

    @circuit(failure_threshold=5, expected_exception=Exception, recovery_timeout=60)
    async def get_real_time_data(self, symbol: str) -> Dict:
        cache_key = f"quote_{symbol.upper()}"
        cached = self._cache.get(cache_key)
        if cached and time.time() - cached[1] < self._cache_ttl_seconds:
            return cached[0]

        params = {"symbol": symbol, "token": self.config.finnhub_key}
        response = await self._client.get("https://finnhub.io/api/v1/quote", params=params)
        response.raise_for_status()
        quote = response.json()

        historical = await self._historical_service.get_historical_data(symbol)
        indicators = self._calculate_indicators(historical)

        payload = {
            "symbol": symbol,
            "current_price": quote.get("c", 0.0),
            "change": quote.get("d", 0.0),
            "change_percent": quote.get("dp", 0.0),
            "high": quote.get("h", 0.0),
            "low": quote.get("l", 0.0),
            "open": quote.get("o", 0.0),
            "previous_close": quote.get("pc", 0.0),
            "indicators": indicators,
            "timestamp": datetime.now().isoformat(),
        }

        self._cache[cache_key] = (payload, time.time())
        return payload

    def _calculate_indicators(self, frame: pd.DataFrame) -> Dict:
        if frame.empty or len(frame) < 20:
            return {}
        closes = frame["close"].astype(float).tolist()
        highs = frame["high"].astype(float).tolist()
        lows = frame["low"].astype(float).tolist()
        volumes = frame["volume"].astype(float).tolist()

        engine = self._technical_engine
        rsi_result = engine.calculate_rsi(closes, period=14)
        macd_result, macd_hist = engine.calculate_macd(closes)

        sma20 = engine.calculate_sma(closes, 20)
        sma50 = engine.calculate_sma(closes, 50)
        ema12 = engine.calculate_ema(closes, 12)
        ema26 = engine.calculate_ema(closes, 26)
        atr14 = engine.calculate_atr(highs, lows, closes, 14)

        # Simple Bollinger calculation
        closes_array = np.array(closes)
        if len(closes_array) >= 20:
            bb_middle = engine.calculate_sma(closes, 20)
            std_dev = np.std(closes_array[-20:])
            bb_upper = bb_middle + (2 * std_dev)
            bb_lower = bb_middle - (2 * std_dev)
        else:
            bb_middle = closes_array[-1]
            bb_upper = bb_middle * 1.02
            bb_lower = bb_middle * 0.98

        # STochastic using pure numpy
        if len(highs) >= 14:
            highest_high = max(highs[-14:])
            lowest_low = min(lows[-14:])
            current_close = closes[-1]
            stoch_k = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100 if highest_high != lowest_low else 50.0
            stoch_d = stoch_k
        else:
            stoch_k = stoch_d = 50.0

        obv = self._calculate_obv(closes, volumes)

        return {
            "sma_20": sma20,
            "sma_50": sma50,
            "ema_12": ema12,
            "ema_26": ema26,
            "rsi_14": rsi_result.value,
            "macd": macd_result.value,
            "macd_signal": macd_result.value - macd_hist,
            "macd_hist": macd_hist,
            "stoch_k": stoch_k,
            "stoch_d": stoch_d,
            "bb_upper": bb_upper,
            "bb_middle": bb_middle,
            "bb_lower": bb_lower,
            "atr_14": atr14,
            "obv": obv,
        }

    def _calculate_obv(self, closes: List[float], volumes: List[float]) -> float:
        if not closes or not volumes:
            return 0.0
        obv = 0.0
        for idx in range(1, len(closes)):
            if closes[idx] > closes[idx - 1]:
                obv += volumes[idx]
            elif closes[idx] < closes[idx - 1]:
                obv -= volumes[idx]
        return obv


class TradingStrategyEngine:
    def __init__(self) -> None:
        self._strategies = {
            "momentum": self._momentum_strategy,
            "mean_reversion": self._mean_reversion_strategy,
            "breakout": self._breakout_strategy,
        }

    async def generate_signals(self, market_data: Dict) -> List[TradingSignal]:
        signals: List[TradingSignal] = []
        for name, func in self._strategies.items():
            signal = await func(market_data)
            if signal:
                signals.append(signal)
        return signals

    async def _momentum_strategy(self, data: Dict) -> Optional[TradingSignal]:
        indicators = data.get("indicators", {})
        price = data.get("current_price", 0.0)
        if price <= 0:
            return None
        score = 0.0
        rationale: List[str] = []
        rsi = indicators.get("rsi_14", 50.0)
        if 40 <= rsi <= 70:
            score += 0.3
            rationale.append(f"RSI {rsi:.1f}")
        if indicators.get("macd_hist", 0.0) > 0:
            score += 0.3
            rationale.append("MACD positive")
        if price > indicators.get("sma_20", price) and price > indicators.get("sma_50", price):
            score += 0.4
            rationale.append("Price above SMAs")

        signal_type = TradingSignalType.NEUTRAL
        if score >= 0.8:
            signal_type = TradingSignalType.STRONG_BUY
        elif score >= 0.6:
            signal_type = TradingSignalType.BUY
        elif score <= 0.2:
            signal_type = TradingSignalType.SELL

        if signal_type == TradingSignalType.NEUTRAL:
            return None
        atr = indicators.get("atr_14", price * 0.02)
        stop_loss = price - (atr * 1.5)
        take_profit = price + (atr * 2.5)
        return TradingSignal(
            symbol=data["symbol"],
            signal_type=signal_type,
            strategy="momentum",
            confidence=score,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            rationale=" | ".join(rationale),
            timestamp=datetime.now(),
        )

    async def _mean_reversion_strategy(self, data: Dict) -> Optional[TradingSignal]:
        indicators = data.get("indicators", {})
        price = data.get("current_price", 0.0)
        if price <= 0:
            return None
        bb_upper = indicators.get("bb_upper")
        bb_lower = indicators.get("bb_lower")
        bb_middle = indicators.get("bb_middle")
        if not all(v is not None for v in (bb_upper, bb_lower, bb_middle)):
            return None

        rationale: List[str] = []
        if price < bb_lower:
            rationale.append("Price below lower Bollinger band")
            signal_type = TradingSignalType.BUY
        elif price > bb_upper:
            rationale.append("Price above upper Bollinger band")
            signal_type = TradingSignalType.SELL
        else:
            return None

        distance = abs(price - bb_middle) / bb_middle if bb_middle else 0.0
        confidence = min(1.0, 0.5 + distance)
        atr = indicators.get("atr_14", price * 0.02)
        if signal_type == TradingSignalType.BUY:
            stop_loss = price - atr
            take_profit = bb_middle
        else:
            stop_loss = price + atr
            take_profit = bb_middle

        return TradingSignal(
            symbol=data["symbol"],
            signal_type=signal_type,
            strategy="mean_reversion",
            confidence=confidence,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            rationale=" | ".join(rationale),
            timestamp=datetime.now(),
        )

    async def _breakout_strategy(self, data: Dict) -> Optional[TradingSignal]:
        indicators = data.get("indicators", {})
        price = data.get("current_price", 0.0)
        if price <= 0:
            return None
        bb_upper = indicators.get("bb_upper", price)
        bb_lower = indicators.get("bb_lower", price)
        atr = indicators.get("atr_14", price * 0.02)

        width = (bb_upper - bb_lower) / price if price else 0.0
        score = 0.0
        rationale: List[str] = []
        if width < 0.04:
            score += 0.3
            rationale.append("Low volatility setup")
        if price > bb_upper:
            score += 0.4
            rationale.append("Breakout above resistance")
            signal_type = TradingSignalType.BUY
        elif price < bb_lower:
            score += 0.4
            rationale.append("Breakdown below support")
            signal_type = TradingSignalType.SELL
        else:
            return None

        if score < 0.6:
            return None

        if signal_type == TradingSignalType.BUY:
            stop_loss = price - atr * 2
            take_profit = price + atr * 3
        else:
            stop_loss = price + atr * 2
            take_profit = price - atr * 3

        return TradingSignal(
            symbol=data["symbol"],
            signal_type=signal_type,
            strategy="breakout",
            confidence=score,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            rationale=" | ".join(rationale),
            timestamp=datetime.now(),
        )


class TradingService:
    """Main trading service entry point for Stage 3."""

    def __init__(
        self,
        config: TradingConfig,
        preferences_manager: TradingPreferencesManagerEnterprise | None = None,
    ) -> None:
        self.config = config
        self.data_service = MarketDataService(config)
        self.strategy_engine = TradingStrategyEngine()
        self.preferences_manager = preferences_manager or TradingPreferencesManagerEnterprise()
        self.execution_service = ExecutionService()
        self._metrics = {
            "api_calls": 0,
            "api_errors": 0,
            "signals_generated": 0,
            "circuit_breaker_trips": 0,
            "last_signal_latency_ms": 0.0,
            "executed_trades": 0,
            "buy_orders": 0,
            "sell_orders": 0,
            "win_trades": 0,
            "loss_trades": 0,
            "projected_roi_sum": 0.0,
            "projected_roi_avg": 0.0,
            "orders_submitted": 0,
            "orders_filled": 0,
            "orders_rejected": 0,
            "execution_notional": 0.0,
            "execution_slippage_bps_sum": 0.0,
            "execution_slippage_bps_avg": 0.0,
            "execution_latency_ms_sum": 0.0,
            "execution_latency_ms_avg": 0.0,
            "execution_latency_ms_last": 0.0,
            "execution_runs": 0,
        }
        self._health = {
            "finnhub": "unknown",
            "strategies": "unknown",
            "status": "unknown",
            "timestamp": datetime.now().isoformat(),
        }
        logger.info("TradingService initialised")

    def _emit_trade_telemetry(self, intent: Dict, trade_result: Dict, success: bool) -> None:
        if emit_training_event is None:
            return
        session_id = intent.get("session_id", "unknown")
        best_signal = intent.get("best_signal") or {}
        symbol = intent.get("symbol") or best_signal.get("symbol")
        confidence = best_signal.get("confidence") or intent.get("confidence")
        preferences_hash = intent.get("preferences", {}).get("integrity_hash")

        roi = None
        entry_price = best_signal.get("entry_price")
        take_profit = best_signal.get("take_profit")
        action = intent.get("action", "").lower()
        if isinstance(entry_price, (int, float)) and isinstance(take_profit, (int, float)) and entry_price:
            raw_roi = (take_profit - entry_price) / float(entry_price)
            roi = -raw_roi if action == "sell" else raw_roi
        elif success:
            roi = 0.0
        else:
            roi = -1.0

        payload = {
            "session_id": session_id,
            "intent": "trading.execute_trade",
            "skill": "trading",
            "feedback_type": "trade_outcome",
            "score": self._roi_to_score(roi),
            "trade": {"symbol": symbol, "roi": roi},
            "preferences": {"integrity_hash": preferences_hash} if preferences_hash else None,
            "confidence": confidence,
        }
        emit_training_event({k: v for k, v in payload.items() if v is not None})

    @staticmethod
    def _roi_to_score(roi: Optional[float]) -> float:
        if roi is None:
            return 0.5
        try:
            return max(0.0, min(1.0, 0.5 + (roi / 0.1)))
        except Exception:
            return 0.5

    async def shutdown(self) -> None:
        await self.data_service.shutdown()

    async def get_signals(self, symbol: str) -> Dict:
        with span_async("TradingService.get_signals", {"symbol": symbol}):
            self._metrics["api_calls"] += 1
            try:
                start = time.time()
                market_data = await self._get_market_data_with_retry(symbol)
                if not market_data:
                    self._metrics["api_errors"] += 1
                    self._health["status"] = "degraded"
                    self._health["timestamp"] = datetime.now().isoformat()
                    return {"error": f"No market data available for {symbol}"}
                signals = await self.strategy_engine.generate_signals(market_data)
                self._metrics["signals_generated"] += len(signals)
                latency = time.time() - start
                self._metrics["last_signal_latency_ms"] = latency * 1000.0
                logger.debug("Signal generation latency %.3fs", latency)
                self._health["status"] = "healthy"
                self._health["timestamp"] = datetime.now().isoformat()
                return {
                    "symbol": symbol,
                    "signals": [self._serialise_signal(signal) for signal in signals],
                    "timestamp": datetime.now().isoformat(),
                    "metrics": {"latency_seconds": latency},
                }
            except circuit.CircuitBreakerError:
                self._metrics["circuit_breaker_trips"] += 1
                logger.warning("Circuit breaker open for market data service")
                self._health["status"] = "degraded"
                self._health["timestamp"] = datetime.now().isoformat()
                return {"error": "Market data service temporarily unavailable"}
            except Exception as exc:
                self._metrics["api_errors"] += 1
                logger.exception("Failed to get trading signals for %s: %s", symbol, exc)
                self._health["status"] = "unhealthy"
                self._health["timestamp"] = datetime.now().isoformat()
                return {"error": str(exc)}

    async def execute_trade(self, intent: Dict) -> Dict:
        with span_async(
            "TradingService.execute_trade",
            {"symbol": intent.get("symbol"), "action": intent.get("action")},
        ):
            symbol = intent.get("symbol", "").upper()
            action = intent.get("action", "").lower()
            if not symbol or action not in {"buy", "sell", "signal"}:
                return {"status": "error", "message": "Invalid trade intent"}
            if action == "signal":
                return await self.get_signals(symbol)
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info("Received trade intent %s %s", action, symbol)
            result = {
                "status": "pending",
                "message": f"{action.upper()} order for {symbol} queued",
                "order_id": order_id,
                "timestamp": datetime.now().isoformat(),
            }
            self._emit_trade_telemetry(intent, result, success=True)
            return result

    async def portfolio_snapshot(self) -> Dict:
        return {
            "total_value": self.config.initial_capital,
            "cash": self.config.initial_capital * 0.5,
            "positions": [],
            "unrealised_pnl": 0.0,
            "daily_pnl": 0.0,
            "timestamp": datetime.now().isoformat(),
        }

    async def run_portfolio_execution(
        self,
        market_state: Dict[str, Any],
        intelligence: Optional[Dict[str, Any]] = None,
        price_map: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        with span_async("TradingService.run_portfolio_execution"):
            portfolio = await self.strategy_engine.generate_portfolio(market_state, intelligence=intelligence)
            if price_map is None:
                price_map = market_state.get("prices") or {}
            if price_map:
                self.execution_service.update_price_marks(price_map)
            execution_result = self.execution_service.execute_portfolio(portfolio, price_map=price_map)
            self._update_execution_metrics(execution_result["metrics"])
            return {"portfolio": portfolio, "execution": execution_result}

    def _update_execution_metrics(self, execution_metrics: Dict[str, float]) -> None:
        runs = self._metrics["execution_runs"] + 1
        self._metrics["execution_runs"] = runs
        submitted = int(execution_metrics.get("orders_submitted", 0))
        filled = int(execution_metrics.get("orders_filled", 0))
        rejected = int(execution_metrics.get("orders_rejected", 0))
        notional = float(execution_metrics.get("execution_notional", 0.0))
        slippage_avg = float(execution_metrics.get("execution_slippage_bps_avg", 0.0))
        latency_avg = float(execution_metrics.get("execution_latency_ms_avg", 0.0))
        latency_last = float(execution_metrics.get("execution_latency_ms_last", 0.0))

        self._metrics["orders_submitted"] += submitted
        self._metrics["orders_filled"] += filled
        self._metrics["orders_rejected"] += rejected
        self._metrics["execution_notional"] += notional
        self._metrics["execution_slippage_bps_sum"] += slippage_avg
        self._metrics["execution_latency_ms_sum"] += latency_avg
        self._metrics["execution_slippage_bps_avg"] = (
            self._metrics["execution_slippage_bps_sum"] / max(self._metrics["execution_runs"], 1)
        )
        self._metrics["execution_latency_ms_avg"] = (
            self._metrics["execution_latency_ms_sum"] / max(self._metrics["execution_runs"], 1)
        )
        self._metrics["execution_latency_ms_last"] = latency_last

    def telemetry(self) -> Dict:
        metrics_snapshot = dict(self._metrics)
        metrics_snapshot.setdefault("portfolio_value", self.config.initial_capital)
        metrics_snapshot["active_strategies"] = len(self.strategy_engine._strategies)
        return {"metrics": metrics_snapshot, "health": dict(self._health)}

    def record_projected_trade(self, trade_data: Dict) -> None:
        best_signal = trade_data.get("best_signal") or {}
        action = trade_data.get("action", "signal")
        entry_price = best_signal.get("entry_price")
        take_profit = best_signal.get("take_profit")
        if entry_price in (None, 0) or take_profit is None:
            return
        self._metrics["executed_trades"] += 1
        if action == "sell":
            self._metrics["sell_orders"] += 1
            projected = (entry_price - take_profit) / abs(entry_price)
            is_win = best_signal.get("signal_type") in {"SELL", "STRONG_SELL"}
        else:
            self._metrics["buy_orders"] += 1
            projected = (take_profit - entry_price) / abs(entry_price)
            is_win = best_signal.get("signal_type") in {"BUY", "STRONG_BUY"}
        if is_win:
            self._metrics["win_trades"] += 1
        else:
            self._metrics["loss_trades"] += 1
        self._metrics["projected_roi_sum"] += projected
        trades = self._metrics["executed_trades"]
        if trades:
            self._metrics["projected_roi_avg"] = self._metrics["projected_roi_sum"] / trades

    async def get_personalized_signals(self, symbol: str, session_id: str, user_id: str) -> Dict:
        """Return signals filtered and sized according to user preferences."""
        prefs = await self.preferences_manager.get_preferences(session_id, user_id)
        validation = await self.preferences_manager.validate_trade(
            session_id=session_id,
            user_id=user_id,
            symbol=symbol,
            position_size=self.config.initial_capital * 0.01,
            portfolio_value=self.config.initial_capital,
        )
        if not validation.get("allowed", True):
            return {
                "error": True,
                "response": "This trade conflicts with your preferences: " + "; ".join(validation.get("reasons", [])),
                "validation": validation,
            }
        base = await self.get_signals(symbol)
        if base.get("error"):
            return base
        signals = base.get("signals", [])
        filtered = [signal for signal in signals if self._signal_meets_preferences(signal, prefs)]
        portfolio_value = base.get("metrics", {}).get("portfolio_value", self.config.initial_capital)
        position_size = prefs.get_position_size(portfolio_value)
        return {
            **base,
            "signals": filtered,
            "personalized": {
                "risk_tolerance": prefs.risk_tolerance.value,
                "max_position_size": position_size,
                "preference_fit": self._calculate_preference_fit(filtered, prefs),
                "validation": validation,
            },
        }

    def _signal_meets_preferences(self, signal: Dict, prefs: TradingPreferencesEnterprise) -> bool:
        confidence = signal.get("confidence", 0.0)
        if prefs.risk_tolerance == RiskTolerance.CONSERVATIVE and confidence < 0.8:
            return False
        if prefs.risk_tolerance == RiskTolerance.MODERATE and confidence < 0.6:
            return False
        return True

    def _calculate_preference_fit(self, signals: List[Dict], prefs: TradingPreferencesEnterprise) -> float:
        if not signals:
            return 0.0
        avg_confidence = sum(signal.get("confidence", 0.0) for signal in signals) / len(signals)
        multipliers = {
            RiskTolerance.CONSERVATIVE: 0.8,
            RiskTolerance.MODERATE: 1.0,
            RiskTolerance.AGGRESSIVE: 1.2,
            RiskTolerance.EXTREME: 1.4,
        }
        return min(1.0, avg_confidence * multipliers.get(prefs.risk_tolerance, 1.0))

    async def _get_market_data_with_retry(self, symbol: str, retries: int = 3) -> Optional[Dict]:
        delay = 1.0
        for attempt in range(retries):
            try:
                return await self.data_service.get_real_time_data(symbol)
            except circuit.CircuitBreakerError:
                self._metrics["circuit_breaker_trips"] += 1
                raise
            except Exception as exc:
                logger.debug("Market data attempt %d failed for %s: %s", attempt + 1, symbol, exc)
                if attempt == retries - 1:
                    return None
                await asyncio.sleep(delay)
                delay *= 2

    def _serialise_signal(self, signal: TradingSignal) -> Dict:
        return {
            "strategy": signal.strategy,
            "signal_type": signal.signal_type.value,
            "confidence": round(signal.confidence, 3),
            "entry_price": round(signal.entry_price, 2),
            "stop_loss": round(signal.stop_loss, 2),
            "take_profit": round(signal.take_profit, 2),
            "rationale": signal.rationale,
            "timestamp": signal.timestamp.isoformat(),
        }


_trading_service: Optional[TradingService] = None
_preferences_manager_singleton: Optional[TradingPreferencesManagerEnterprise] = None


async def get_trading_service(
    config: Optional[TradingConfig] = None,
    preferences_manager: Optional[TradingPreferencesManagerEnterprise] = None,
) -> TradingService:
    global _trading_service, _preferences_manager_singleton
    if _trading_service is None:
        if config is None:
            from config.trading_config import get_trading_config  # Lazy import

            config = get_trading_config()
        if preferences_manager is None:
            if _preferences_manager_singleton is None:
                _preferences_manager_singleton = TradingPreferencesManagerEnterprise()
            preferences_manager = _preferences_manager_singleton
        _trading_service = TradingService(config, preferences_manager=preferences_manager)
    return _trading_service


def reset_trading_service() -> None:
    global _trading_service
    _trading_service = None


__all__ = [
    "TradingService",
    "TradingConfig",
    "TradingSignal",
    "TradingSignalType",
    "get_trading_service",
    "reset_trading_service",
]


