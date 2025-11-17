"""Prometheus metrics and monitoring integration."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
except ImportError:  # pragma: no cover - optional dependency
    Counter = Gauge = Histogram = Summary = None  # type: ignore

    def start_http_server(*_args: Any, **_kwargs: Any) -> None:  # type: ignore[override]
        logging.getLogger(__name__).warning("prometheus_client unavailable; metrics server not started.")

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore


logger = logging.getLogger(__name__)


def _safe_gauge(name: str, documentation: str, labelnames: Optional[list[str]] = None, registry: Any = None):
    if Gauge is None:
        return None
    kwargs = {"registry": registry} if registry is not None else {}
    return Gauge(name, documentation, labelnames or [], **kwargs)


def _safe_counter(name: str, documentation: str, labelnames: Optional[list[str]] = None, registry: Any = None):
    if Counter is None:
        return None
    kwargs = {"registry": registry} if registry is not None else {}
    return Counter(name, documentation, labelnames or [], **kwargs)


def _safe_histogram(name: str, documentation: str, labelnames: Optional[list[str]] = None, registry: Any = None):
    if Histogram is None:
        return None
    kwargs = {"registry": registry} if registry is not None else {}
    return Histogram(name, documentation, labelnames or [], **kwargs)


class TradingMetrics:
    """Prometheus metrics for training, strategy, and risk."""

    def __init__(self, port: int = 8000, registry: Any = None) -> None:
        self.port = port
        self.registry = registry

        # Training metrics
        self.training_reward_avg = _safe_gauge("training_reward_avg", "Average training reward", ["agent_type", "market_regime"], registry=registry)
        self.training_loss = _safe_gauge("training_loss", "Training loss value", ["component", "agent_type"], registry=registry)
        self.training_cycles = _safe_counter("training_cycles_total", "Total training cycles", ["training_type"], registry=registry)

        # Strategy metrics
        self.strategy_weight = _safe_gauge("strategy_weight", "Current strategy weight", ["strategy_name", "asset_class"], registry=registry)
        self.strategy_performance = _safe_gauge("strategy_performance", "Strategy performance metric", ["strategy_name", "timeframe"], registry=registry)

        # Risk metrics
        self.risk_drawdown_latest = _safe_gauge("risk_drawdown_latest", "Latest drawdown percentage", registry=registry)
        self.risk_var_95 = _safe_gauge("risk_var_95", "Value at risk 95", registry=registry)
        self.risk_var_99 = _safe_gauge("risk_var_99", "Value at risk 99", registry=registry)
        self.risk_cvar_95 = _safe_gauge("risk_cvar_95", "Conditional value at risk 95", registry=registry)
        self.risk_cvar_99 = _safe_gauge("risk_cvar_99", "Conditional value at risk 99", registry=registry)
        self.risk_leverage = _safe_gauge("risk_leverage", "Portfolio leverage", registry=registry)
        self.risk_volatility = _safe_gauge("risk_volatility", "Portfolio volatility", registry=registry)
        self.risk_sharpe = _safe_gauge("risk_sharpe_ratio", "Portfolio Sharpe ratio", registry=registry)
        self.risk_sortino = _safe_gauge("risk_sortino_ratio", "Portfolio Sortino ratio", registry=registry)
        self.risk_calmar = _safe_gauge("risk_calmar_ratio", "Portfolio Calmar ratio", registry=registry)
        self.risk_max_drawdown = _safe_gauge("risk_max_drawdown", "Maximum drawdown", registry=registry)
        self.risk_herfindahl = _safe_gauge("risk_herfindahl_index", "Herfindahl concentration index", registry=registry)
        self.risk_effective_positions = _safe_gauge("risk_effective_positions", "Effective number of positions", registry=registry)
        self.risk_largest_position = _safe_gauge("risk_largest_position", "Largest position weight", registry=registry)
        self.risk_downside_deviation = _safe_gauge("risk_downside_deviation", "Downside deviation", registry=registry)
        self.risk_omega_ratio = _safe_gauge("risk_omega_ratio", "Omega ratio", registry=registry)
        self.risk_turnover_ratio = _safe_gauge("risk_turnover_ratio", "Turnover ratio", registry=registry)
        self.risk_liquidity_pressure = _safe_gauge("risk_liquidity_pressure", "Liquidity pressure ratio", registry=registry)
        self.risk_gross_exposure_notional = _safe_gauge(
            "risk_gross_exposure_notional", "Gross exposure in notional terms", registry=registry
        )
        self.risk_var_horizons = {
            "1d": _safe_gauge("risk_var_95_h1d", "VaR 95 horizon 1d", registry=registry),
            "5d": _safe_gauge("risk_var_95_h5d", "VaR 95 horizon 5d", registry=registry),
            "21d": _safe_gauge("risk_var_95_h21d", "VaR 95 horizon 21d", registry=registry),
        }
        self.risk_cvar_horizons = {
            "1d": _safe_gauge("risk_cvar_95_h1d", "CVaR 95 horizon 1d", registry=registry),
            "5d": _safe_gauge("risk_cvar_95_h5d", "CVaR 95 horizon 5d", registry=registry),
            "21d": _safe_gauge("risk_cvar_95_h21d", "CVaR 95 horizon 21d", registry=registry),
        }
        self.risk_es_horizons = {
            "1d": _safe_gauge("risk_es_95_h1d", "Expected shortfall 95 horizon 1d", registry=registry),
            "5d": _safe_gauge("risk_es_95_h5d", "Expected shortfall 95 horizon 5d", registry=registry),
            "21d": _safe_gauge("risk_es_95_h21d", "Expected shortfall 95 horizon 21d", registry=registry),
        }
        self.risk_stress_losses = {
            "vol_spike": _safe_gauge("risk_stress_vol_spike", "Stress loss volatility spike", registry=registry),
            "market_crash": _safe_gauge("risk_stress_market_crash", "Stress loss market crash", registry=registry),
            "correlation_break": _safe_gauge(
                "risk_stress_correlation_break", "Stress loss correlation break", registry=registry
            ),
        }

        # Market metrics
        self.market_regime = _safe_gauge("market_regime", "Market regime indicator", ["regime_type"], registry=registry)
        self.volatility_regime = _safe_gauge("volatility_regime", "Volatility regime indicator", ["regime_level"], registry=registry)

        # System performance
        self.inference_latency = _safe_histogram("inference_latency_seconds", "Inference latency seconds", ["model_type"], registry=registry)
        self.feature_engineering_time = _safe_histogram("feature_engineering_seconds", "Feature engineering latency", registry=registry)
        self.queue_depth = _safe_gauge("queue_depth", "Queue depth", ["queue_name"], registry=registry)

        # Drift metrics
        self.feature_drift = _safe_gauge("feature_drift", "Feature drift score", ["feature_name"], registry=registry)
        self.model_drift = _safe_gauge("model_drift", "Model drift value", ["model_name", "metric"], registry=registry)

        if Gauge is not None and registry is None:
            try:
                start_http_server(self.port)
            except OSError as exc:  # pragma: no cover - port already in use
                logger.warning("Prometheus server already running on port %s (%s)", self.port, exc)

    # Update helpers --------------------------------------------------
    def update_training_metrics(self, training_results: Dict[str, Any]) -> None:
        if not self.training_reward_avg or not self.training_loss:
            return
        multi_agent = training_results.get("multi_agent", {})
        for agent, metrics in multi_agent.items():
            reward = metrics.get("reward")
            if reward is not None:
                self.training_reward_avg.labels(agent_type=agent, market_regime=training_results.get("regime", "unknown")).set(reward)
        world_model = training_results.get("world_model", {})
        for loss_name, loss_val in world_model.items():
            if loss_val is not None:
                self.training_loss.labels(component=loss_name, agent_type="world_model").set(loss_val)

    def update_strategy_metrics(self, portfolio_allocation: Dict[str, Dict[str, Any]]) -> None:
        if not self.strategy_weight:
            return
        for strategy_name, allocation in portfolio_allocation.items():
            weight = allocation.get("weight", 0.0)
            asset_class = allocation.get("asset_class", "multi")
            self.strategy_weight.labels(strategy_name=strategy_name, asset_class=asset_class).set(weight)
            performance = allocation.get("performance")
            if performance is not None and self.strategy_performance:
                self.strategy_performance.labels(strategy_name=strategy_name, timeframe="recent").set(performance)

    def update_risk_metrics(self, risk_report: Dict[str, Any]) -> None:
        metrics = risk_report.get("current_metrics", risk_report)
        if self.risk_drawdown_latest:
            self.risk_drawdown_latest.set(metrics.get("current_drawdown", metrics.get("drawdown", 0.0)))
        if self.risk_var_95:
            self.risk_var_95.set(metrics.get("var_95", metrics.get("var", 0.0)))
        if self.risk_var_99:
            self.risk_var_99.set(metrics.get("var_99", metrics.get("var", 0.0)))
        if self.risk_cvar_95:
            self.risk_cvar_95.set(metrics.get("cvar_95", metrics.get("cvar", 0.0)))
        if self.risk_cvar_99:
            self.risk_cvar_99.set(metrics.get("cvar_99", metrics.get("cvar", 0.0)))
        if self.risk_leverage:
            self.risk_leverage.set(metrics.get("leverage", 1.0))
        if self.risk_volatility:
            self.risk_volatility.set(metrics.get("volatility", 0.0))
        if self.risk_sharpe:
            self.risk_sharpe.set(metrics.get("sharpe_ratio", 0.0))
        if self.risk_sortino:
            self.risk_sortino.set(metrics.get("sortino_ratio", 0.0))
        if self.risk_calmar:
            self.risk_calmar.set(metrics.get("calmar_ratio", 0.0))
        if self.risk_max_drawdown:
            self.risk_max_drawdown.set(metrics.get("max_drawdown", 0.0))
        if self.risk_herfindahl:
            self.risk_herfindahl.set(metrics.get("herfindahl_index", 0.0))
        if self.risk_effective_positions:
            self.risk_effective_positions.set(metrics.get("effective_num_positions", 0.0))
        if self.risk_largest_position:
            self.risk_largest_position.set(metrics.get("largest_position", 0.0))
        if self.risk_downside_deviation:
            self.risk_downside_deviation.set(metrics.get("downside_deviation", 0.0))
        if self.risk_omega_ratio:
            self.risk_omega_ratio.set(metrics.get("omega_ratio", 0.0))
        if self.risk_turnover_ratio:
            self.risk_turnover_ratio.set(metrics.get("turnover_ratio", 0.0))
        if self.risk_liquidity_pressure:
            self.risk_liquidity_pressure.set(metrics.get("liquidity_pressure", 0.0))
        if self.risk_gross_exposure_notional:
            self.risk_gross_exposure_notional.set(metrics.get("gross_exposure_notional", 0.0))
        for label, gauge in self.risk_var_horizons.items():
            if gauge:
                gauge.set(metrics.get(f"var_95_h{label}", 0.0))
        for label, gauge in self.risk_cvar_horizons.items():
            if gauge:
                gauge.set(metrics.get(f"cvar_95_h{label}", 0.0))
        for label, gauge in self.risk_es_horizons.items():
            if gauge:
                gauge.set(metrics.get(f"es_95_h{label}", 0.0))
        for name, gauge in self.risk_stress_losses.items():
            if gauge:
                gauge.set(metrics.get(f"stress_{name}", 0.0))

    def update_market_metrics(self, regime_analysis: Dict[str, Any]) -> None:
        if not self.market_regime or not self.volatility_regime:
            return
        regime = regime_analysis.get("current_regime", "unknown")
        volatility = regime_analysis.get("volatility_regime", "normal")
        for regime_type in ["trending_bull", "trending_bear", "ranging", "high_vol", "low_vol", "crash", "rally"]:
            self.market_regime.labels(regime_type=regime_type).set(1.0 if regime_type in regime else 0.0)
        for vol_level in ["low", "normal", "high", "extreme"]:
            self.volatility_regime.labels(regime_level=vol_level).set(1.0 if vol_level in volatility else 0.0)

    def record_inference_latency(self, model_type: str, start_time: float) -> None:
        if not self.inference_latency:
            return
        latency = time.time() - start_time
        self.inference_latency.labels(model_type=model_type).observe(latency)

    def record_feature_engineering_time(self, start_time: float) -> None:
        if not self.feature_engineering_time:
            return
        latency = time.time() - start_time
        self.feature_engineering_time.observe(latency)

    def update_queue_metrics(self, queue_depths: Dict[str, int]) -> None:
        if not self.queue_depth:
            return
        for queue_name, depth in queue_depths.items():
            self.queue_depth.labels(queue_name=queue_name).set(depth)

    def update_drift_metrics(self, drift_analysis: Dict[str, Any]) -> None:
        if self.feature_drift:
            for feature, score in drift_analysis.get("feature_drift", {}).items():
                self.feature_drift.labels(feature_name=feature).set(score)
        if self.model_drift:
            for model_name, metrics in drift_analysis.get("model_drift", {}).items():
                for metric_name, value in metrics.items():
                    self.model_drift.labels(model_name=model_name, metric=metric_name).set(value)


@dataclass(slots=True)
class AdvancedRiskMetrics:
    """Advanced risk analytics with Prometheus integration."""

    metrics: TradingMetrics
    history_limit: int = 1000
    risk_history: list[Dict[str, Any]] = field(default_factory=list, init=False)

    def calculate_advanced_risk_metrics(self, portfolio: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, float]:
        returns = portfolio.get("returns", [])
        if np is None or not returns:
            risk_metrics = {
                "var_95": 0.0,
                "var_99": 0.0,
                "cvar_95": 0.0,
                "cvar_99": 0.0,
                "current_drawdown": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0,
                "expected_return": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "calmar_ratio": 0.0,
                "leverage_ratio": portfolio.get("leverage", 1.0),
            }
        else:
            arr = np.asarray(returns)
            var = float(np.percentile(arr, 5))
            var_99 = float(np.percentile(arr, 1))
            tail = arr[arr <= var]
            cvar = float(tail.mean()) if len(tail) else var
            tail_99 = arr[arr <= var_99]
            cvar_99 = float(tail_99.mean()) if len(tail_99) else var_99
            cumulative = np.cumprod(1 + arr)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = (cumulative - running_max) / running_max
            current_drawdown = float(drawdowns[-1]) if len(drawdowns) else 0.0
            max_drawdown = float(drawdowns.min()) if len(drawdowns) else 0.0
            mean_ret = float(arr.mean())
            volatility = float(arr.std(ddof=1))
            downside = arr[arr < 0]
            downside_std = float(downside.std(ddof=1)) if len(downside) >= 2 else 0.0
            eps = 1e-12
            sharpe = (mean_ret / (volatility + eps)) * np.sqrt(252)
            sortino = (mean_ret / (downside_std + eps)) * np.sqrt(252)
            calmar = mean_ret / (abs(max_drawdown) + eps)
            risk_metrics = {
                "var_95": var,
                "var_99": var_99,
                "cvar_95": cvar,
                "cvar_99": cvar_99,
                "current_drawdown": current_drawdown,
                "max_drawdown": max_drawdown,
                "expected_return": mean_ret,
                "volatility": volatility,
                "sharpe_ratio": sharpe,
                "sortino_ratio": sortino,
                "calmar_ratio": calmar,
                "leverage_ratio": portfolio.get("leverage", 1.0),
            }
        self.metrics.update_risk_metrics(risk_metrics)
        self.risk_history.append({"timestamp": datetime.now(timezone.utc).isoformat(), **risk_metrics})
        if len(self.risk_history) > self.history_limit:
            self.risk_history = self.risk_history[-self.history_limit :]
        return risk_metrics


@dataclass(slots=True)
class MonitoringIntegration:
    """Wraps component instrumentation for monitoring."""

    config: Dict[str, Any]
    metrics: TradingMetrics = field(init=False)
    risk_metrics: AdvancedRiskMetrics = field(init=False)

    def __post_init__(self) -> None:
        port = self.config.get("metrics_port", 8000)
        self.metrics = TradingMetrics(port=port)
        self.risk_metrics = AdvancedRiskMetrics(self.metrics)

    async def instrument_training_system(self, training_system: Any) -> None:
        original_cycle = getattr(training_system, "_advanced_training_cycle", None)
        if not callable(original_cycle):
            logger.warning("Training system missing _advanced_training_cycle; skipping instrumentation.")
            return

        async def instrumented_cycle(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await original_cycle(*args, **kwargs)
                self.metrics.update_training_metrics(result or {})
                if self.metrics.training_cycles:
                    self.metrics.training_cycles.labels(training_type="advanced").inc()
                self.metrics.record_feature_engineering_time(start_time)
                return result
            except Exception:
                if self.metrics.training_cycles:
                    self.metrics.training_cycles.labels(training_type="failed").inc()
                raise

        training_system._advanced_training_cycle = instrumented_cycle

    async def instrument_risk_system(self, risk_orchestrator: Any) -> None:
        original_optimize = getattr(risk_orchestrator, "optimize_portfolio", None)
        if not callable(original_optimize):
            logger.warning("Risk orchestrator missing optimize_portfolio; skipping instrumentation.")
            return

        def instrumented_optimize(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            portfolio = original_optimize(*args, **kwargs)
            if isinstance(portfolio, dict):
                self.risk_metrics.calculate_advanced_risk_metrics(portfolio, {})
            self.metrics.record_inference_latency("risk_optimizer", start_time)
            return portfolio

        risk_orchestrator.optimize_portfolio = instrumented_optimize

    async def instrument_strategy_engine(self, strategy_engine: Any) -> None:
        original_generate = getattr(strategy_engine, "generate_portfolio", None)
        if not callable(original_generate):
            logger.warning("Strategy engine missing generate_portfolio; skipping instrumentation.")
            return

        async def instrumented_generate(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            portfolio = await original_generate(*args, **kwargs)
            allocations = portfolio.get("allocations") if isinstance(portfolio, dict) else None
            if allocations:
                self.metrics.update_strategy_metrics(allocations)
            regime = kwargs.get("regime")
            if regime:
                self.metrics.update_market_metrics({"current_regime": regime})
            self.metrics.record_inference_latency("strategy_engine", start_time)
            return portfolio

        strategy_engine.generate_portfolio = instrumented_generate


async def setup_comprehensive_monitoring(
    config: Dict[str, Any],
    training_system: Any,
    risk_orchestrator: Any,
    strategy_engine: Any,
) -> MonitoringIntegration:
    """Instrument systems and launch background monitoring tasks."""

    integration = MonitoringIntegration(config)
    await integration.instrument_training_system(training_system)
    await integration.instrument_risk_system(risk_orchestrator)
    await integration.instrument_strategy_engine(strategy_engine)
    asyncio.create_task(_monitor_queues(integration))
    asyncio.create_task(_monitor_drift(integration))
    logger.info("Monitoring integration complete; Prometheus on port %s", integration.metrics.port)
    return integration


async def _monitor_queues(integration: MonitoringIntegration) -> None:
    while True:
        try:
            queue_depths = await _fetch_queue_depths()
            integration.metrics.update_queue_metrics(queue_depths)
            await asyncio.sleep(30)
        except Exception as exc:  # pragma: no cover
            logger.warning("Queue monitoring error: %s", exc)
            await asyncio.sleep(60)


async def _monitor_drift(integration: MonitoringIntegration) -> None:
    while True:
        try:
            drift = await _fetch_drift_metrics()
            integration.metrics.update_drift_metrics(drift)
            await asyncio.sleep(300)
        except Exception as exc:  # pragma: no cover
            logger.warning("Drift monitoring error: %s", exc)
            await asyncio.sleep(600)


async def _fetch_queue_depths() -> Dict[str, int]:
    return {"training-telemetry": 0, "market-data": 0, "trading-signals": 0}


async def _fetch_drift_metrics() -> Dict[str, Any]:
    return {"feature_drift": {}, "model_drift": {}}

