"""
Feature engineering layer that converts intelligence bundles into RL-friendly tensors.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

import numpy as np
import torch

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    state_dim: int = 512
    max_correlation_features: int = 32
    max_volatility_features: int = 16
    max_regime_features: int = 16
    portfolio_feature_dim: int = 32


class IntelligenceFeatureEngine:
    """Transforms heterogeneous intelligence outputs into fixed-length state vectors."""

    def __init__(self, config: FeatureConfig | Dict[str, Any] | None = None) -> None:
        if isinstance(config, dict):
            self.config = FeatureConfig(**config)
        elif isinstance(config, FeatureConfig):
            self.config = config
        else:
            self.config = FeatureConfig()
        self._feature_stats: Dict[str, torch.Tensor] = {}

    # ------------------------------------------------------------------ #
    def intelligence_to_state(self, intelligence: Dict[str, Any], portfolio_state: Dict[str, Any]) -> torch.Tensor:
        try:
            components = [
                self._correlation_features(intelligence.get("correlation_intelligence", {})),
                self._volatility_features(intelligence.get("volatility_intelligence", {})),
                self._regime_features(intelligence.get("regime_shift_intelligence", {})),
                self._risk_features(intelligence, portfolio_state),
                self._opportunity_features(intelligence),
                self._portfolio_features(portfolio_state),
                self._insight_features(intelligence.get("cross_dimensional_insights", {})),
                self._confidence_features(intelligence.get("meta_confidence_scores", {})),
            ]
            raw = torch.cat(components)
        except Exception as exc:  # pragma: no cover - defensive path
            logger.error("Failed to create features: %s", exc)
            return torch.zeros(self.config.state_dim)

        padded = self._project(raw)
        self._update_stats(padded)
        return padded

    # ------------------------------------------------------------------ #
    def _correlation_features(self, corr: Dict[str, Any]) -> torch.Tensor:
        summary = corr.get("correlation_matrix", {}).get("summary", {})
        regime = corr.get("correlation_regime", {})
        vector = [
            float(summary.get("mean", 0.0)),
            float(summary.get("std", 0.0)),
            float(summary.get("min", 0.0)),
            float(summary.get("max", 0.0)),
            float(regime.get("stability", 0.5)),
            float(regime.get("mean", 0.0)),
            float(regime.get("volatility", 0.0)),
            float(corr.get("data_quality_score", 0.5)),
        ]
        tail = corr.get("tail_dependencies", {})
        if tail:
            lower = [deps.get("lower_tail", 0.0) for deps in tail.values()]
            upper = [deps.get("upper_tail", 0.0) for deps in tail.values()]
            vector.extend([float(np.mean(lower)), float(np.mean(upper))])
        network = corr.get("correlation_network", {})
        vector.append(float(network.get("density", 0.0)))
        vector.append(float(network.get("clustering", {}).get(next(iter(network.get("clustering", {})), ""), 0.0)))
        return torch.tensor(vector, dtype=torch.float32)

    def _volatility_features(self, vol: Dict[str, Any]) -> torch.Tensor:
        probs = vol.get("regime_probabilities", {})
        clustering = vol.get("clustering_metrics", {})
        vrp = vol.get("vrp_analysis", {})
        vector = [
            float(probs.get("high_vol", 0.0)),
            float(probs.get("normal", 0.0)),
            float(probs.get("low_vol", 0.0)),
            float(vol.get("volatility_metrics", {}).get("portfolio_volatility", 0.0)),
            float(vol.get("volatility_metrics", {}).get("volatility_trend", 0.0)),
            float(clustering.get("hurst_exponent", 0.5)),
            float(clustering.get("average_regime_duration", 0.0)),
            float(vol.get("data_quality_score", 0.5)),
        ]
        if vrp:
            premiums = [item.get("volatility_risk_premium", 0.0) for item in vrp.values()]
            if premiums:
                vector.append(float(np.mean(premiums)))
                vector.append(float(np.std(premiums)))
        return torch.tensor(vector, dtype=torch.float32)

    def _regime_features(self, regime: Dict[str, Any]) -> torch.Tensor:
        current = regime.get("current_regime", {})
        stability = regime.get("regime_stability", {})
        warnings = regime.get("early_warnings", {}).get("composite_early_warning", {})
        return torch.tensor(
            [
                self._encode_regime(current.get("type", "unknown")),
                float(stability.get("stability_score", 0.5)),
                float(stability.get("volatility_stability", 0.5)),
                float(stability.get("skew_risk", 0.5)),
                float(warnings.get("score", 0.0)),
                float(warnings.get("confidence", 0.0)),
            ],
            dtype=torch.float32,
        )

    def _risk_features(self, intelligence: Dict[str, Any], portfolio: Dict[str, Any]) -> torch.Tensor:
        health = intelligence.get("cross_dimensional_insights", {}).get("composite_market_health", {})
        risk_metrics = intelligence.get("risk_intelligence", {}).get("metrics", {})
        if not risk_metrics:
            risk_metrics = portfolio.get("risk_metrics", {})
        return torch.tensor(
            [
                float(health.get("composite_score", 0.5)),
                float(risk_metrics.get("current_drawdown", 0.0)),
                float(risk_metrics.get("max_drawdown", 0.0)),
                float(risk_metrics.get("var_95", 0.0)),
                float(risk_metrics.get("var_99", 0.0)),
                float(risk_metrics.get("cvar_95", 0.0)),
                float(risk_metrics.get("cvar_99", 0.0)),
                float(risk_metrics.get("var_95_h1d", 0.0)),
                float(risk_metrics.get("cvar_95_h5d", 0.0)),
                float(risk_metrics.get("es_95_h21d", 0.0)),
                float(risk_metrics.get("volatility", 0.0)),
                float(risk_metrics.get("sharpe_ratio", 0.0)),
                float(risk_metrics.get("sortino_ratio", 0.0)),
                float(risk_metrics.get("downside_deviation", 0.0)),
                float(risk_metrics.get("omega_ratio", 0.0)),
                float(risk_metrics.get("herfindahl_index", 0.0)),
                float(risk_metrics.get("largest_position", 0.0)),
                float(risk_metrics.get("turnover_ratio", 0.0)),
                float(risk_metrics.get("liquidity_pressure", 0.0)),
                float(risk_metrics.get("stress_market_crash", 0.0)),
                float(risk_metrics.get("stress_vol_spike", 0.0)),
            ],
            dtype=torch.float32,
        )

    def _opportunity_features(self, intelligence: Dict[str, Any]) -> torch.Tensor:
        funding = intelligence.get("funding_intelligence", {}).get("arbitrage_opportunities", {})
        count = float(funding.get("profitable", 0))
        sharpe = intelligence.get("sharpe_intelligence", {}).get("multi_timeframe_sharpe", {})
        best_sharpe = max((metrics.get("sharpe_ratio", 0.0) for metrics in sharpe.values()), default=0.0)
        return torch.tensor([count, float(best_sharpe)], dtype=torch.float32)

    def _portfolio_features(self, portfolio: Dict[str, Any]) -> torch.Tensor:
        positions = portfolio.get("positions", {})
        weights = [pos.get("weight", 0.0) for pos in positions.values()] if positions else []
        return torch.tensor(
            [
                float(portfolio.get("current_value", 0.0)),
                float(portfolio.get("cash_balance", 0.0)),
                float(portfolio.get("leverage", 1.0)),
                float(len(positions)),
                float(max(weights) if weights else 0.0),
                float(np.std(weights) if weights else 0.0),
            ],
            dtype=torch.float32,
        )

    def _insight_features(self, insights: Dict[str, Any]) -> torch.Tensor:
        impacts = {"high": 0, "medium": 0, "low": 0}
        confidences: List[float] = []
        for data in insights.values():
            if not isinstance(data, dict):
                continue
            impact = data.get("impact", "low")
            impacts[impact] = impacts.get(impact, 0) + 1
            confidences.append(float(data.get("confidence", 0.0)))
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return torch.tensor([impacts["high"], impacts["medium"], impacts["low"], avg_conf], dtype=torch.float32)

    def _confidence_features(self, scores: Dict[str, float]) -> torch.Tensor:
        if not scores:
            return torch.tensor([0.5, 0.0, 0.1, 0.9], dtype=torch.float32)
        values = list(scores.values())
        return torch.tensor(
            [float(np.mean(values)), float(np.std(values)), float(np.min(values)), float(np.max(values))],
            dtype=torch.float32,
        )

    # ------------------------------------------------------------------ #
    def _project(self, features: torch.Tensor) -> torch.Tensor:
        if features.numel() == self.config.state_dim:
            return features
        if features.numel() > self.config.state_dim:
            return features[: self.config.state_dim]
        padding = torch.zeros(self.config.state_dim - features.numel())
        return torch.cat([features, padding])

    def _update_stats(self, features: torch.Tensor) -> None:
        if "mean" not in self._feature_stats:
            self._feature_stats["mean"] = features.clone()
            self._feature_stats["var"] = torch.zeros_like(features)
            self._feature_stats["count"] = torch.tensor(1.0)
            return

        count = self._feature_stats["count"]
        mean = self._feature_stats["mean"]
        var = self._feature_stats["var"]

        count_new = count + 1
        delta = features - mean
        mean_new = mean + delta / count_new
        var_new = var + delta * (features - mean_new)

        self._feature_stats["count"] = count_new
        self._feature_stats["mean"] = mean_new
        self._feature_stats["var"] = var_new

    # ------------------------------------------------------------------ #
    @staticmethod
    def _encode_regime(regime: str) -> float:
        mapping = {
            "high_volatility": 0.8,
            "trending_bull": 0.6,
            "trending_bear": 0.4,
            "ranging": 0.5,
            "normal": 0.55,
        }
        return float(mapping.get(regime, 0.5))

