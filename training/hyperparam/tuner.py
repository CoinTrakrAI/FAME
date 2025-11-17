"""
Hyperparameter tuning utilities with simple Bayesian-inspired random search and bandit updates.
"""

from __future__ import annotations

import itertools
import logging
import math
import random
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


ObjectiveFn = Callable[[Dict[str, Any]], float]


@dataclass(slots=True)
class HyperparameterConfig:
    search_space: Dict[str, Sequence[Any]]
    max_trials: int = 20
    exploration_ratio: float = 0.3
    seed: Optional[int] = None


@dataclass(slots=True)
class TuningResult:
    params: Dict[str, Any]
    score: float
    trial_index: int


class HyperparameterTuner:
    """
    Lightweight hyperparameter tuner using epsilon-greedy random search across search space.
    """

    def __init__(self, config: HyperparameterConfig, objective: ObjectiveFn) -> None:
        if not config.search_space:
            raise ValueError("Hyperparameter search space must not be empty.")
        self.config = config
        self.objective = objective
        self._results: List[TuningResult] = []
        if config.seed is not None:
            random.seed(config.seed)

    def run(self) -> List[TuningResult]:
        logger.info(
            "Starting hyperparameter tuning",
            extra={
                "max_trials": self.config.max_trials,
                "exploration_ratio": self.config.exploration_ratio,
            },
        )

        candidates = list(self._enumerate_candidates())
        random.shuffle(candidates)
        trial_count = min(self.config.max_trials, len(candidates))
        exploitation_pool: List[TuningResult] = []

        for trial_index in range(trial_count):
            explore = random.random() < self.config.exploration_ratio or not exploitation_pool
            if explore:
                params = candidates.pop() if candidates else self._sample_random()
            else:
                params = self._select_from_pool(exploitation_pool)

            score = self._safe_objective(params)
            result = TuningResult(params=params, score=score, trial_index=trial_index)
            self._results.append(result)
            exploitation_pool.append(result)
            exploitation_pool = sorted(exploitation_pool, key=lambda r: r.score, reverse=True)[:5]
            logger.debug("Trial %s -> score %.4f params=%s", trial_index, score, params)

        self._results.sort(key=lambda r: r.score, reverse=True)
        logger.info("Tuning completed with best score %.4f", self._results[0].score if self._results else float("nan"))
        return list(self._results)

    def best(self) -> Optional[TuningResult]:
        return self._results[0] if self._results else None

    # ------------------------------------------------------------------ #
    def _enumerate_candidates(self) -> Iterable[Dict[str, Any]]:
        keys = list(self.config.search_space.keys())
        values = [self.config.search_space[key] for key in keys]
        if all(len(vals) <= 10 for vals in values) and math.prod(len(vals) for vals in values) <= 200:
            for combination in itertools.product(*values):
                yield dict(zip(keys, combination))
        else:
            # fall back to random sampling
            for _ in range(self.config.max_trials * 2):
                yield self._sample_random()

    def _sample_random(self) -> Dict[str, Any]:
        return {
            key: random.choice(list(values))
            for key, values in self.config.search_space.items()
        }

    def _select_from_pool(self, pool: List[TuningResult]) -> Dict[str, Any]:
        weights = [max(result.score, 1e-9) for result in pool]
        chosen = random.choices(pool, weights=weights, k=1)[0]
        perturbation = {}
        for param, values in self.config.search_space.items():
            values_list = list(values)
            if chosen.params.get(param) in values_list and len(values_list) > 1:
                idx = values_list.index(chosen.params[param])
                neighbours = [values_list[(idx - 1) % len(values_list)], values_list[(idx + 1) % len(values_list)]]
                perturbation[param] = random.choice(neighbours)
            else:
                perturbation[param] = random.choice(values_list)
        new_params = dict(chosen.params)
        new_params.update(perturbation)
        return new_params

    def _safe_objective(self, params: Dict[str, Any]) -> float:
        try:
            score = float(self.objective(params))
        except Exception as exc:  # pragma: no cover
            logger.error("Objective function failed for params %s: %s", params, exc)
            score = float("-inf")
        return score

