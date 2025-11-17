"""Strategy engine integrating features, regime detection, and risk orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from features import AdvancedFeatureEngine
from regimes import RegimeDetectionEngine
from regimes.regime_types import MarketRegime
from risk import RiskOrchestrator
from strategies import HierarchicalStrategyController
from strategies.strategy_base import TradingSignal
from orchestrator.allocation import (
    AllocationConfig,
    apply_position_scales,
    risk_parity_allocation,
)


@dataclass(slots=True)
class StrategyEngine:
    feature_engine: AdvancedFeatureEngine = field(default_factory=AdvancedFeatureEngine)
    regime_engine: RegimeDetectionEngine = field(default_factory=RegimeDetectionEngine)
    controller: HierarchicalStrategyController = field(default_factory=HierarchicalStrategyController)
    risk_orchestrator: RiskOrchestrator = field(default_factory=RiskOrchestrator)
    target_var_95: float = 0.04
    min_confidence: float = 0.2
    allocation_config: AllocationConfig = field(default_factory=AllocationConfig)

    async def generate_portfolio(
        self,
        raw_market_data: Dict,
        intelligence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        enriched = await self.feature_engine.generate_features(raw_market_data)
        market_data = {**raw_market_data, **enriched}
        regime_override = self._resolve_regime(intelligence)
        strategy_confidence = self._strategy_confidence(intelligence)

        regime, signals, strategy_weights = await self.controller.decide_action(
            market_data,
            regime_override=regime_override,
            strategy_confidence=strategy_confidence,
        )

        risk_metrics = self._extract_risk_metrics(intelligence)
        global_confidence = float(
            (intelligence or {})
            .get("unified_signals", {})
            .get("meta", {})
            .get("confidence", 1.0)
        )
        global_confidence = max(self.min_confidence, min(1.0, global_confidence))
        risk_scale = self._risk_scale(risk_metrics)

        raw_positions = self._compose_positions(signals, global_confidence, risk_scale)
        allocated_positions, allocation_weights = self._apply_allocation(
            raw_positions, market_data, intelligence, risk_metrics
        )
        adjusted_positions = self.risk_orchestrator.apply(allocated_positions)

        metadata = {
            "regime": regime.value if isinstance(regime, MarketRegime) else str(regime),
            "strategy_weights": strategy_weights,
            "allocation_weights": allocation_weights,
            "risk_scale": risk_scale,
            "global_confidence": global_confidence,
            "risk_metrics": risk_metrics,
        }
        allocations = {name: {"weight": weight} for name, weight in strategy_weights.items()}
        raw_signal_dump = {
            asset: {
                "strategy": signal.strategy,
                "direction": signal.direction,
                "size": signal.size,
                "confidence": signal.confidence,
            }
            for asset, signal in signals.items()
        }

        return {
            "positions": adjusted_positions,
            "raw_positions": raw_positions,
            "raw_signals": raw_signal_dump,
            "allocations": allocations,
            "metadata": metadata,
        }

    # ------------------------------------------------------------------ #
    def _resolve_regime(self, intelligence: Optional[Dict[str, Any]]) -> Optional[MarketRegime]:
        if not intelligence:
            return None
        regime_data = (
            intelligence.get("regime_shift_intelligence", {})
            .get("current_regime", {})
            .get("type")
        )
        if not regime_data:
            return None
        try:
            return MarketRegime(regime_data)
        except ValueError:
            return None

    def _strategy_confidence(self, intelligence: Optional[Dict[str, Any]]) -> Dict[str, float]:
        if not intelligence:
            return {}
        overrides = intelligence.get("strategy_confidence", {})
        if overrides:
            return {name: max(0.0, float(value)) for name, value in overrides.items()}

        meta_conf = float(
            intelligence.get("unified_signals", {}).get("meta", {}).get("confidence", 1.0)
        )
        strategies = self.controller.strategy_universe.get_strategies().keys()
        return {name: max(self.min_confidence, min(1.0, meta_conf)) for name in strategies}

    def _extract_risk_metrics(self, intelligence: Optional[Dict[str, Any]]) -> Dict[str, float]:
        if not intelligence:
            return {}
        return intelligence.get("risk_intelligence", {}).get("metrics", {})

    def _risk_scale(self, risk_metrics: Dict[str, float]) -> float:
        if not risk_metrics:
            return 1.0

        scale = 1.0
        var_95 = abs(risk_metrics.get("var_95", 0.0))
        if var_95:
            scale = min(scale, self.target_var_95 / max(var_95, 1e-6))

        cvar_99 = abs(risk_metrics.get("cvar_99", 0.0))
        if cvar_99:
            scale = min(scale, (self.target_var_95 * 1.5) / max(cvar_99, 1e-6))

        max_drawdown = abs(risk_metrics.get("max_drawdown", 0.0))
        dd_limit = self.risk_orchestrator.constraints.max_drawdown
        if max_drawdown and max_drawdown > dd_limit:
            scale = min(scale, dd_limit / max_drawdown)

        return float(max(0.05, min(1.0, scale)))

    def _compose_positions(
        self,
        signals: Dict[str, TradingSignal],
        global_confidence: float,
        risk_scale: float,
    ) -> Dict[str, float]:
        positions: Dict[str, float] = {}
        for asset, signal in signals.items():
            position = (
                signal.size
                * signal.direction
                * signal.confidence
                * global_confidence
                * risk_scale
            )
            positions[asset] = position
        return positions

    def _apply_allocation(
        self,
        positions: Dict[str, float],
        market_data: Dict[str, Any],
        intelligence: Optional[Dict[str, Any]],
        risk_metrics: Dict[str, float],
    ) -> tuple[Dict[str, float], Dict[str, float]]:
        if not positions:
            return positions, {}

        asset_vol = self._asset_volatility(positions, market_data, intelligence)
        weights = risk_parity_allocation(positions.keys(), asset_vol)

        total_exposure = sum(abs(size) for size in positions.values())
        total_exposure = max(total_exposure, self.allocation_config.min_allocation)

        scaled: Dict[str, float] = {}
        for asset, base_position in positions.items():
            weight = weights.get(asset, 0.0)
            direction = 1.0 if base_position >= 0 else -1.0
            target_size = total_exposure * weight * direction
            target_size = max(
                -self.allocation_config.max_allocation,
                min(self.allocation_config.max_allocation, target_size),
            )
            scaled[asset] = target_size

        current_var = abs(risk_metrics.get("var_95", 0.0))
        scaled = apply_position_scales(
            scaled,
            self.allocation_config.target_volatility,
            current_var,
            self.allocation_config.max_leverage,
        )
        return scaled, weights

    def _asset_volatility(
        self,
        positions: Dict[str, float],
        market_data: Dict[str, Any],
        intelligence: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        vol_map: Dict[str, float] = {}
        if intelligence:
            vol_metrics = (
                intelligence.get("volatility_intelligence", {})
                .get("volatility_metrics", {})
                .get("asset_volatility", {})
            )
            for asset, vol in vol_metrics.items():
                vol_map[asset] = abs(float(vol)) or 0.2

        if not vol_map:
            raw_vol = market_data.get("asset_volatility", {})
            for asset, vol in raw_vol.items():
                vol_map[asset] = abs(float(vol)) or 0.2

        if not vol_map:
            for asset in market_data.get("momentum", {}).keys():
                vol_map[asset] = 0.2

        if not vol_map:
            for asset in market_data.get("returns", []):
                vol_map[asset] = 0.2
        if not vol_map:
            vol_map = {asset: 0.2 for asset in positions.keys()}

        return vol_map

