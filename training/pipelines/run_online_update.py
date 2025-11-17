"""Online training loop for continuous adaptation."""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from statistics import fmean
from typing import Deque, Dict, Iterable, Optional

import yaml

from analytics.feature_store import FeatureStore
from training.context import TrainingContext
from training.rewards import RewardEngine

try:
    from intelligence.reinforcement_trainer import ReinforcementTrainer
except ImportError:  # pragma: no cover - optional dependency
    ReinforcementTrainer = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OnlinePolicyTrainer:
    """Consume streaming feedback and perform incremental updates."""

    context: TrainingContext
    buffer_size: int = 500
    max_kl_divergence: float = 0.15
    feature_store: FeatureStore = field(default_factory=FeatureStore)
    _buffer: Deque[Dict] = field(default_factory=deque, init=False)
    _trainer: Optional[ReinforcementTrainer] = field(default=None, init=False)
    _reward_engine: RewardEngine = field(init=False)
    _recent_reward_mean: Optional[float] = field(default=None, init=False)

    def __post_init__(self) -> None:
        config = self._load_config()
        online_cfg = config.get("online", {})
        evaluation_cfg = config.get("evaluation", {})
        self.buffer_size = int(online_cfg.get("buffer_size", self.buffer_size))
        self.max_kl_divergence = float(evaluation_cfg.get("drift_kl_threshold", self.max_kl_divergence))
        self._reward_engine = RewardEngine.from_file(self.context.reward_schema_path)
        if ReinforcementTrainer is not None:
            self._trainer = ReinforcementTrainer()

    def _load_config(self) -> Dict:
        path = self.context.config_path
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def enqueue(self, event: Dict) -> None:
        self._buffer.append(event)
        if len(self._buffer) > self.buffer_size * 2:
            self._buffer.popleft()

    async def drain(self, events: Iterable[Dict]) -> None:
        for event in events:
            self.enqueue(event)
        if self.should_update():
            await self.perform_update()

    def should_update(self) -> bool:
        return len(self._buffer) >= self.buffer_size and self._trainer is not None

    async def perform_update(self) -> None:
        if not self._trainer or not self._buffer:
            return
        batch = list(self._buffer)
        rewards = [self._reward_engine.compute(event) for event in batch]
        avg_reward = fmean(rewards) if rewards else 0.0

        if self._recent_reward_mean is not None:
            drift = abs(avg_reward - self._recent_reward_mean)
            if drift > self.max_kl_divergence:
                logger.warning(
                    "Online trainer drift threshold exceeded; skipping update",
                    extra={
                        "run_id": self.context.run_id,
                        "drift": drift,
                        "threshold": self.max_kl_divergence,
                    },
                )
                self._buffer.clear()
                self._recent_reward_mean = avg_reward
                return

        logger.info(
            "Running online trainer update",
            extra={"run_id": self.context.run_id, "batch_size": len(batch), "avg_reward": avg_reward},
        )
        metrics = await self._trainer.train_from_events(batch, rewards)  # type: ignore[union-attr]
        self._recent_reward_mean = avg_reward
        self.feature_store.save_dataset(f"{self.context.run_id}_online", self._normalise_records(batch, rewards))
        logger.debug("Online trainer metrics", extra={"run_id": self.context.run_id, **metrics})
        self._buffer.clear()

    def _normalise_records(self, events: Iterable[Dict], rewards: Iterable[float]) -> Iterable[Dict]:
        for event, reward in zip(events, rewards):
            record = dict(event)
            record["reward"] = reward
            record["run_id"] = self.context.run_id
            yield record

    async def run_loop(self, source: asyncio.Queue) -> None:
        """Simple async loop for integration tests."""
        while True:
            event = await source.get()
            if event is None:
                logger.info("Online trainer stopping")
                break
            await self.drain([event])

