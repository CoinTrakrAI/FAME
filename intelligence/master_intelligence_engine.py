"""
Master intelligence engine that orchestrates all advanced analytical modules.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from risk.risk_orchestrator import RiskOrchestrator
except ImportError:  # pragma: no cover
    RiskOrchestrator = None  # type: ignore


@dataclass
class IntelligenceBundle:
    """Container that holds a full snapshot of market intelligence."""

    timestamp: str
    correlation_intelligence: Dict[str, Any]
    volatility_intelligence: Dict[str, Any]
    sharpe_intelligence: Dict[str, Any]
    delta_neutral_intelligence: Dict[str, Any]
    open_interest_intelligence: Dict[str, Any]
    funding_intelligence: Dict[str, Any]
    regime_shift_intelligence: Dict[str, Any]
    risk_intelligence: Dict[str, Any]
    cross_dimensional_insights: Dict[str, Any]
    meta_confidence_scores: Dict[str, float]
    unified_signals: Dict[str, Any]
    processing_latency: float

    @property
    def as_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "correlation_intelligence": self.correlation_intelligence,
            "volatility_intelligence": self.volatility_intelligence,
            "sharpe_intelligence": self.sharpe_intelligence,
            "delta_neutral_intelligence": self.delta_neutral_intelligence,
            "open_interest_intelligence": self.open_interest_intelligence,
            "funding_intelligence": self.funding_intelligence,
            "regime_shift_intelligence": self.regime_shift_intelligence,
            "risk_intelligence": self.risk_intelligence,
            "cross_dimensional_insights": self.cross_dimensional_insights,
            "meta_confidence_scores": self.meta_confidence_scores,
            "unified_signals": self.unified_signals,
            "processing_latency": self.processing_latency,
        }


class MasterIntelligenceEngine:
    """Coordinates all intelligence modules, producing a holistic insight bundle."""

    DEFAULT_TIMEOUT = 30.0

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        self._module_timeout = float(self.config.get("module_timeout", self.DEFAULT_TIMEOUT))
        self._meta_confidence_history: Dict[str, list[float]] = {}
        self.intelligence_modules: Dict[str, Any] = {}
        self.risk_orchestrator: Optional[RiskOrchestrator] = None
        if RiskOrchestrator is not None:
            provided = self.config.get("risk_orchestrator")
            self.risk_orchestrator = provided if isinstance(provided, RiskOrchestrator) else RiskOrchestrator()
        self._initialize_modules()
        logger.info("MasterIntelligenceEngine initialised with %d modules", len(self.intelligence_modules))

    # --------------------------------------------------------------------- #
    # Module initialisation
    # --------------------------------------------------------------------- #
    def _initialize_modules(self) -> None:
        module_map = {
            "correlation": ("intelligence.correlation_intelligence", "AdvancedCorrelationEngine", FallbackCorrelationEngine),
            "volatility": ("intelligence.volatility_intelligence", "AdvancedVolatilityEngine", FallbackVolatilityEngine),
            "sharpe": ("intelligence.sharpe_intelligence", "AdvancedSharpeEngine", FallbackEngine),
            "delta_neutral": ("intelligence.delta_neutral_intelligence", "AdvancedDeltaNeutralEngine", FallbackEngine),
            "open_interest": ("intelligence.open_interest_intelligence", "AdvancedOpenInterestEngine", FallbackEngine),
            "funding": ("intelligence.funding_intelligence", "AdvancedFundingEngine", FallbackEngine),
            "regime_shift": ("intelligence.regime_shift_intelligence", "AdvancedRegimeShiftEngine", FallbackEngine),
        }

        for key, (module_path, class_name, fallback_cls) in module_map.items():
            instance = self._import_engine(module_path, class_name, fallback_cls, key)
            self.intelligence_modules[key] = instance

    @staticmethod
    def _import_engine(
        module_path: str, class_name: str, fallback_cls: type, module_name: str
    ) -> Any:
        try:
            module = importlib.import_module(module_path)
            engine_cls = getattr(module, class_name)
            return engine_cls()
        except Exception as exc:  # pragma: no cover - defensive path
            logger.warning("Falling back for %s engine: %s", module_name, exc)
            return fallback_cls(module_name)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    async def generate_comprehensive_intelligence(self, market_data: Dict[str, Any]) -> IntelligenceBundle:
        start_time = datetime.now(timezone.utc)

        results = await self._execute_modules_parallel(market_data)
        risk_snapshot = self._risk_snapshot(market_data)
        if risk_snapshot is not None:
            results["risk"] = risk_snapshot
        cross_insights = self._cross_dimensional_insights(results)
        meta_confidence = self._calculate_meta_confidence(results)
        unified_signals = self._generate_unified_signals(results, cross_insights)

        processing_latency = (datetime.now(timezone.utc) - start_time).total_seconds()

        return IntelligenceBundle(
            timestamp=datetime.now(timezone.utc).isoformat(),
            correlation_intelligence=results.get("correlation", {}),
            volatility_intelligence=results.get("volatility", {}),
            sharpe_intelligence=results.get("sharpe", {}),
            delta_neutral_intelligence=results.get("delta_neutral", {}),
            open_interest_intelligence=results.get("open_interest", {}),
            funding_intelligence=results.get("funding", {}),
            regime_shift_intelligence=results.get("regime_shift", {}),
            risk_intelligence=results.get("risk", {}),
            cross_dimensional_insights=cross_insights,
            meta_confidence_scores=meta_confidence,
            unified_signals=unified_signals,
            processing_latency=processing_latency,
        )

    # --------------------------------------------------------------------- #
    # Module execution helpers
    # --------------------------------------------------------------------- #
    async def _execute_modules_parallel(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        tasks = {
            name: asyncio.create_task(self._execute_single_module(name, module, market_data))
            for name, module in self.intelligence_modules.items()
        }
        done, pending = await asyncio.wait(tasks.values(), timeout=self._module_timeout, return_when=asyncio.ALL_COMPLETED)

        results: Dict[str, Any] = {}
        for task in done:
            name, result = task.result()
            results[name] = result

        for task in pending:
            task.cancel()
            name = self._task_to_module_name(tasks, task)
            logger.warning("Module %s timed out after %.1fs", name, self._module_timeout)
            results[name] = self._timeout_result(name)

        return results

    @staticmethod
    def _task_to_module_name(task_map: Dict[str, asyncio.Task], target: asyncio.Task) -> str:
        for module_name, task in task_map.items():
            if task is target:
                return module_name
        return "unknown"

    async def _execute_single_module(self, name: str, module: Any, market_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        start = datetime.now(timezone.utc)
        try:
            if hasattr(module, "analyze"):
                result = await module.analyze(market_data)  # type: ignore[attr-defined]
            else:
                result = await module.generate_analysis(market_data)  # type: ignore[attr-defined]
        except Exception as exc:
            logger.error("Module %s failed: %s", name, exc)
            result = {"error": str(exc)}

        result.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        result["processing_time"] = (datetime.now(timezone.utc) - start).total_seconds()
        return name, result

    @staticmethod
    def _timeout_result(name: str) -> Dict[str, Any]:
        return {
            "error": "timeout",
            "module": name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_time": float("nan"),
        }

    # --------------------------------------------------------------------- #
    # Insight synthesis
    # --------------------------------------------------------------------- #
    def _cross_dimensional_insights(self, intelligence: Dict[str, Any]) -> Dict[str, Any]:
        insights: Dict[str, Any] = {}

        volatility = intelligence.get("volatility", {})
        correlation = intelligence.get("correlation", {})
        regime = intelligence.get("regime_shift", {})
        open_interest = intelligence.get("open_interest", {})
        funding = intelligence.get("funding", {})
        sharpe = intelligence.get("sharpe", {})
        risk = intelligence.get("risk", {}).get("metrics", {})

        # Example: market stress
        if (
            volatility.get("current_regime") == "high_volatility"
            and correlation.get("correlation_regime", {}).get("stability", 0.5) < 0.3
        ):
            insights["market_stress_signal"] = {
                "confidence": 0.85,
                "impact": "high",
                "recommendation": "reduce_exposure",
                "rationale": "High volatility coinciding with unstable correlations signals systemic stress.",
            }

        # Example: gamma squeeze
        if (
            regime.get("transition_probabilities", {}).get("ensemble_max", 0.0) > 0.7
            and open_interest.get("total_concentration", 0.0) > 0.4
        ):
            insights["gamma_squeeze_risk"] = {
                "confidence": 0.75,
                "impact": "medium",
                "recommendation": "monitor_option_flow",
            }

        # Example: funding arbitrage caution
        profitable_arbs = funding.get("arbitrage_opportunities", {}).get("profitable", 0)
        if profitable_arbs and volatility.get("regime_probabilities", {}).get("high_vol", 0) > 0.6:
            insights["volatile_funding_arbitrage"] = {
                "confidence": 0.65,
                "impact": "medium",
                "recommendation": "size_positions_cautiously",
            }

        if risk and risk.get("herfindahl_index", 0.0) > 0.25:
            insights["concentration_risk"] = {
                "confidence": min(0.9, risk["herfindahl_index"]),
                "impact": "medium",
                "recommendation": "diversify_positions",
                "details": {"herfindahl_index": risk["herfindahl_index"]},
            }

        insights["composite_market_health"] = self._market_health_score(intelligence)
        insights["performance_stability"] = {
            "sharpe_stability": sharpe.get("stability_score", 0.5),
            "regime_stability": regime.get("regime_stability", {}).get("stability_score", 0.5),
        }
        return insights

    def _market_health_score(self, intelligence: Dict[str, Any]) -> Dict[str, Any]:
        components = {
            "volatility": 1.0 - intelligence.get("volatility", {}).get("regime_probabilities", {}).get("high_vol", 0.0),
            "correlation": intelligence.get("correlation", {}).get("correlation_regime", {}).get("stability", 0.5),
            "regime": intelligence.get("regime_shift", {}).get("regime_stability", {}).get("stability_score", 0.5),
            "liquidity": intelligence.get("open_interest", {}).get("liquidity_score", 0.6),
        }
        weights = {"volatility": 0.3, "correlation": 0.25, "regime": 0.25, "liquidity": 0.2}
        score = sum(components[key] * weights[key] for key in components)
        level = "healthy"
        if score < 0.4:
            level = "stressed"
        elif score < 0.7:
            level = "moderate"
        return {"composite_score": score, "component_scores": components, "health_level": level}

    # --------------------------------------------------------------------- #
    # Meta confidence
    # --------------------------------------------------------------------- #
    def _calculate_meta_confidence(self, intelligence: Dict[str, Any]) -> Dict[str, float]:
        confidence: Dict[str, float] = {}
        for name, result in intelligence.items():
            if result.get("error"):
                score = 0.1
            else:
                stability = result.get("stability_score", result.get("regime_stability", 0.6))
                data_quality = result.get("data_quality_score", 0.8)
                score = max(0.05, min(1.0, float(stability) * float(data_quality)))
            confidence[name] = score
            history = self._meta_confidence_history.setdefault(name, [])
            history.append(score)
            if len(history) > 200:
                history[:] = history[-200:]
        return confidence

    # --------------------------------------------------------------------- #
    # Unified signals
    # --------------------------------------------------------------------- #
    def _generate_unified_signals(self, intelligence: Dict[str, Any], insights: Dict[str, Any]) -> Dict[str, Any]:
        signals: Dict[str, Any] = {}

        regime = intelligence.get("regime_shift", {})
        volatility = intelligence.get("volatility", {})
        funding = intelligence.get("funding", {})
        risk = intelligence.get("risk", {})

        signals["regime"] = regime.get("current_regime", {}).get("type", "normal")
        signals["high_volatility"] = volatility.get("current_regime") == "high_volatility"
        signals["funding_opportunities"] = funding.get("arbitrage_opportunities", {})
        metrics = risk.get("metrics", {})
        if metrics:
            signals["risk_posture"] = {
                "var_95": metrics.get("var_95"),
                "cvar_99": metrics.get("cvar_99"),
                "max_drawdown": metrics.get("max_drawdown"),
                "leverage": metrics.get("leverage", 1.0),
            }
            signals["risk_scenarios"] = risk.get("scenarios", {})

        signals["meta"] = {
            "confidence": float(sum(self._meta_confidence_history.get(k, [0])[-1] for k in self.intelligence_modules))
            / max(1, len(self.intelligence_modules)),
            "insight_count": len(insights),
        }
        signals["risk"] = {"health_level": insights.get("composite_market_health", {}).get("health_level", "unknown")}
        return signals

    def _risk_snapshot(self, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.risk_orchestrator:
            return None

        if "portfolio_returns" in market_data:
            self.risk_orchestrator.extend_returns(market_data["portfolio_returns"])
        elif market_data.get("portfolio_return") is not None:
            self.risk_orchestrator.record_return(float(market_data["portfolio_return"]))

        positions = market_data.get("positions")
        leverage = float(market_data.get("leverage", 1.0))
        portfolio_value = market_data.get("portfolio_value")

        metrics = self.risk_orchestrator.risk_metrics(
            leverage=leverage,
            positions=positions,
            portfolio_value=portfolio_value,
        )
        scenarios = self.risk_orchestrator.scenario_analysis(
            portfolio_value=portfolio_value or metrics.get("portfolio_value", 0.0) or 0.0,
            leverage=leverage,
        )
        return {
            "metrics": metrics,
            "scenarios": scenarios,
            "history": self.risk_orchestrator.metrics_history[-30:],
            "data_quality_score": 0.8 if metrics.get("observation_count", 0) > 30 else 0.5,
            "stability_score": max(0.1, 1.0 - abs(metrics.get("current_drawdown", 0.0))),
        }


# =============================================================================
# Fallback implementations
# =============================================================================
class FallbackEngine:
    """Generic fallback returning minimal structure."""

    def __init__(self, module_name: str) -> None:
        self.module_name = module_name

    async def analyze(self, _market_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "fallback": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stability_score": 0.5,
            "data_quality_score": 0.5,
        }


class FallbackCorrelationEngine(FallbackEngine):
    async def analyze(self, _market_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await super().analyze(_market_data)
        result.update({"correlation_regime": {"regime": "unknown", "stability": 0.5}})
        return result


class FallbackVolatilityEngine(FallbackEngine):
    async def analyze(self, _market_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await super().analyze(_market_data)
        result.update({"current_regime": "normal", "regime_probabilities": {"normal": 1.0}})
        return result

