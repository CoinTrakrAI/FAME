"""
Advanced correlation analysis with rolling metrics, tail dependence, and graph analytics.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:  # optional dependency
    import networkx as nx

    HAS_NETWORKX = True
except Exception:  # pragma: no cover - defensive fallback
    HAS_NETWORKX = False
    nx = None  # type: ignore
    logger.warning("networkx not available; correlation network metrics disabled.")


class AdvancedCorrelationEngine:
    """Performs multidimensional correlation analysis."""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._rolling_windows = self.config.get("rolling_windows", [5, 20, 60])
        self._max_pairs = int(self.config.get("max_pairs", 30))
        self._history: List[Dict[str, Any]] = []

    async def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        prices = market_data.get("prices")
        if not prices:
            return self._error_result("missing_price_data")

        price_df = self._to_dataframe(prices)
        if price_df.shape[1] < 2 or len(price_df) < 5:
            return self._error_result("insufficient_assets")

        returns = price_df.pct_change().dropna(how="all")
        if returns.empty:
            return self._error_result("insufficient_returns")

        result: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "assets": list(returns.columns),
        }

        corr_matrix = returns.corr().fillna(0.0)
        result["correlation_matrix"] = self._serialise_corr_matrix(corr_matrix)
        result["rolling_correlations"] = self._rolling_statistics(returns)
        result["correlation_regime"] = self._detect_regime(result["rolling_correlations"])
        result["tail_dependencies"] = self._tail_dependencies(returns)
        result["lead_lag"] = self._lead_lag_analysis(returns)
        result["regime_stability"] = self._regime_stability()
        result["data_quality_score"] = self._data_quality_score(returns)
        if HAS_NETWORKX:
            result["correlation_network"] = self._build_network(corr_matrix)
        else:
            result["correlation_network"] = {"warning": "networkx_unavailable"}

        self._history.append(
            {
                "timestamp": result["timestamp"],
                "regime": result["correlation_regime"]["regime"],
                "stability": result["correlation_regime"]["stability"],
            }
        )
        if len(self._history) > 500:
            self._history = self._history[-250:]

        return result

    # ------------------------------------------------------------------ #
    # Core analytics
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_dataframe(prices: Dict[str, Any]) -> pd.DataFrame:
        if isinstance(prices, pd.DataFrame):
            return prices.copy()
        return pd.DataFrame(prices).sort_index()

    def _serialise_corr_matrix(self, matrix: pd.DataFrame) -> Dict[str, Any]:
        tri = matrix.values[np.triu_indices_from(matrix.values, k=1)]
        summary = {
            "mean": float(np.nanmean(tri)) if len(tri) else 0.0,
            "median": float(np.nanmedian(tri)) if len(tri) else 0.0,
            "std": float(np.nanstd(tri)) if len(tri) else 0.0,
            "min": float(np.nanmin(tri)) if len(tri) else 0.0,
            "max": float(np.nanmax(tri)) if len(tri) else 0.0,
        }
        return {"assets": matrix.columns.tolist(), "matrix": matrix.values.tolist(), "summary": summary}

    def _rolling_statistics(self, returns: pd.DataFrame) -> Dict[str, Any]:
        rolling: Dict[str, Any] = {}
        for window in self._rolling_windows:
            if len(returns) < window:
                continue
            window_key = f"window_{window}"
            correlations = returns.rolling(window=window).corr()
            latest = correlations.iloc[-returns.shape[1] :]
            matrix = latest.values.reshape(returns.shape[1], returns.shape[1])
            rolling[window_key] = {
                "matrix": matrix.tolist(),
                "mean": float(np.nanmean(matrix)),
                "std": float(np.nanstd(matrix)),
            }
        return rolling

    def _detect_regime(self, rolling: Dict[str, Any]) -> Dict[str, Any]:
        stats = [data["mean"] for data in rolling.values() if "mean" in data]
        dispersion = [data["std"] for data in rolling.values() if "std" in data]
        if not stats:
            return {"regime": "unknown", "stability": 0.5}

        mean_corr = float(np.mean(stats))
        vol_corr = float(np.mean(dispersion)) if dispersion else 0.0

        if vol_corr > 0.3:
            regime, stability = "unstable", 0.2
        elif abs(mean_corr) > 0.7:
            regime, stability = ("highly_positive" if mean_corr > 0 else "highly_negative", 0.8)
        elif abs(mean_corr) < 0.2:
            regime, stability = "diversified", 0.6
        else:
            regime, stability = "moderate", 0.7
        return {"regime": regime, "stability": stability, "mean": mean_corr, "volatility": vol_corr}

    def _tail_dependencies(self, returns: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        assets = returns.columns.tolist()
        limit = min(self._max_pairs, len(assets) * (len(assets) - 1) // 2)
        dependencies: Dict[str, Dict[str, float]] = {}

        idx = 0
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                if idx >= limit:
                    break
                r1, r2 = returns[assets[i]].dropna(), returns[assets[j]].dropna()
                common = r1.index.intersection(r2.index)
                if len(common) < 20:
                    continue
                series1, series2 = r1.loc[common].values, r2.loc[common].values
                lower_threshold1 = np.percentile(series1, 5)
                lower_threshold2 = np.percentile(series2, 5)
                upper_threshold1 = np.percentile(series1, 95)
                upper_threshold2 = np.percentile(series2, 95)

                lower_joint = np.mean((series1 <= lower_threshold1) & (series2 <= lower_threshold2))
                upper_joint = np.mean((series1 >= upper_threshold1) & (series2 >= upper_threshold2))

                dependencies[f"{assets[i]}::{assets[j]}"] = {
                    "lower_tail": float(lower_joint / 0.05 if 0.05 else 0.0),
                    "upper_tail": float(upper_joint / 0.05 if 0.05 else 0.0),
                    "tail_asymmetry": float((upper_joint - lower_joint) / 0.05),
                }
                idx += 1
        return dependencies

    def _lead_lag_analysis(self, returns: pd.DataFrame, max_lag: int = 5) -> Dict[str, Any]:
        assets = returns.columns.tolist()
        analysis: Dict[str, Any] = {}
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                series1 = returns[assets[i]].dropna()
                series2 = returns[assets[j]].dropna()
                common = series1.index.intersection(series2.index)
                if len(common) < max_lag * 2:
                    continue
                s1, s2 = series1.loc[common], series2.loc[common]
                best_lag, best_corr = 0, 0.0
                for lag in range(-max_lag, max_lag + 1):
                    if lag < 0:
                        corr = s1.iloc[:lag].corr(s2.iloc[-lag:])
                    elif lag > 0:
                        corr = s1.iloc[lag:].corr(s2.iloc[:-lag])
                    else:
                        corr = s1.corr(s2)
                    corr = 0.0 if np.isnan(corr) else float(corr)
                    if abs(corr) > abs(best_corr):
                        best_corr, best_lag = corr, lag
                analysis[f"{assets[i]}->{assets[j]}"] = {"optimal_lag": best_lag, "correlation": best_corr}
        return analysis

    def _regime_stability(self) -> float:
        if len(self._history) < 5:
            return 0.5
        recent = [entry["regime"] for entry in self._history[-20:]]
        diversity = len(set(recent))
        stability = 1.0 - (diversity - 1) / max(1, len(recent))
        return float(max(0.1, min(1.0, stability)))

    @staticmethod
    def _data_quality_score(returns: pd.DataFrame) -> float:
        if returns.empty:
            return 0.0
        missing = returns.isna().sum().sum() / (returns.shape[0] * returns.shape[1])
        variance = returns.var().replace(0, np.nan)
        variance_stability = 1.0 - np.nanstd(variance) / (np.nanmean(variance) + 1e-12)
        observations = min(1.0, len(returns) / 250)
        quality = (1 - missing) * variance_stability * observations
        return float(max(0.1, min(1.0, quality)))

    def _build_network(self, corr_matrix: pd.DataFrame) -> Dict[str, Any]:
        if not HAS_NETWORKX:
            return {"error": "networkx_unavailable"}
        graph = nx.Graph()
        assets = corr_matrix.columns.tolist()
        for asset in assets:
            graph.add_node(asset)
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                weight = float(corr_matrix.iloc[i, j])
                if abs(weight) >= 0.3:
                    graph.add_edge(assets[i], assets[j], weight=weight)

        if graph.number_of_edges() == 0:
            return {"warning": "no_significant_edges"}

        centrality = nx.degree_centrality(graph)
        betweenness = nx.betweenness_centrality(graph)
        clustering = nx.clustering(graph)
        density = nx.density(graph)
        try:
            communities = nx.algorithms.community.greedy_modularity_communities(graph)
            community_map = {f"community_{idx}": list(comm) for idx, comm in enumerate(communities)}
        except Exception:
            community_map = {}
        return {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "density": density,
            "degree_centrality": centrality,
            "betweenness_centrality": betweenness,
            "clustering": clustering,
            "communities": community_map,
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _error_result(reason: str) -> Dict[str, Any]:
        return {"error": reason, "timestamp": datetime.now(timezone.utc).isoformat(), "correlation_regime": {"regime": "unknown", "stability": 0.5}}

