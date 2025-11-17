"""
Live intelligence-driven training loop that continuously ingests market intelligence.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
import torch

from intelligence.master_intelligence_engine import IntelligenceBundle, MasterIntelligenceEngine
from training.intelligence_features import IntelligenceFeatureEngine
from training.multi_agent_rl import MultiAgentConfig, MultiAgentRLSystem
from training.monitoring import PerformanceSnapshot, TrainingPerformanceTracker
from training.replay import ExperienceBuffer
from training.scheduler import AutoRetrainScheduler, RetrainConfig

logger = logging.getLogger(__name__)


class LiveIntelligenceTrainer:
    """Coordinates intelligence generation and learning updates."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.training_interval = float(config.get("training_interval", 60.0))
        self.max_buffer = int(config.get("max_buffer_size", 10_000))

        self.intelligence_engine = MasterIntelligenceEngine(config.get("intelligence"))
        feature_cfg = config.get("feature_engine")
        self.feature_engine = IntelligenceFeatureEngine(feature_cfg)
        ma_config = MultiAgentConfig(**config.get("multi_agent", {}))
        self.multi_agent = MultiAgentRLSystem(ma_config)

        self.is_running = False
        self._performance_history: List[Dict[str, Any]] = []
        self.current_intelligence: IntelligenceBundle | None = None
        self.performance_tracker = TrainingPerformanceTracker()

        experience_cfg = config.get("experience_buffer", {})
        persist_path = experience_cfg.get("persist_path")
        self.experience_buffer = ExperienceBuffer(
            capacity=int(experience_cfg.get("capacity", self.max_buffer)),
            ttl_seconds=experience_cfg.get("ttl_seconds"),
            persistence_path=Path(persist_path) if persist_path else None,
        )
        self.replay_sample_size = int(experience_cfg.get("sample_size", 0))
        scheduler_cfg = config.get("auto_retrain")
        self.retrain_scheduler: Optional[AutoRetrainScheduler] = None
        self.retrain_events: List[Dict[str, Any]] = []
        if scheduler_cfg:
            retrain_config = RetrainConfig(
                reward_drop_threshold=scheduler_cfg.get("reward_drop_threshold", 0.15),
                win_rate_threshold=scheduler_cfg.get("win_rate_threshold", 0.45),
                drift_threshold=scheduler_cfg.get("drift_threshold", 0.4),
                min_buffer_size=scheduler_cfg.get("min_buffer_size", 500),
                cooldown_minutes=scheduler_cfg.get("cooldown_minutes", 120),
            )
            self.retrain_scheduler = AutoRetrainScheduler(
                retrain_config,
                callback=self._on_retrain_decision,
            )

    async def start(self) -> None:
        self.is_running = True
        logger.info("Live intelligence trainer started.")

        while self.is_running:
            cycle_start = datetime.now(timezone.utc)
            try:
                await self._training_cycle()
            except Exception as exc:  # pragma: no cover - runtime protection
                logger.exception("Training cycle failure: %s", exc)
                await asyncio.sleep(60)
            else:
                elapsed = (datetime.now(timezone.utc) - cycle_start).total_seconds()
                sleep_for = max(1.0, self.training_interval - elapsed)
                await asyncio.sleep(sleep_for)

    async def _training_cycle(self) -> None:
        market_data = await self._collect_market_data()
        if not market_data:
            logger.debug("Skipping cycle due to missing market data.")
            return

        self.current_intelligence = await self.intelligence_engine.generate_comprehensive_intelligence(market_data)

        telemetry = await self._collect_telemetry()
        if not telemetry:
            logger.debug("No telemetry available for training.")
            return

        experiences = self._build_experiences(self.current_intelligence, telemetry)
        if not experiences:
            logger.debug("No experiences generated for this cycle.")
            return

        self.experience_buffer.add_many(experiences)
        train_batch = list(experiences)
        if self.replay_sample_size > 0:
            replay_batch = self.experience_buffer.sample(self.replay_sample_size)
            if replay_batch:
                train_batch.extend(replay_batch)

        await self.multi_agent.train_cycle(market_data, train_batch)
        self._log_performance(experiences, telemetry)

    # ------------------------------------------------------------------ #
    def _build_experiences(
        self, intelligence: IntelligenceBundle, telemetry: Sequence[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        experiences: List[Dict[str, Any]] = []
        for event in telemetry:
            portfolio_state = event.get("portfolio_state", {})
            state_tensor = self.feature_engine.intelligence_to_state(intelligence.as_dict, portfolio_state)

            reward = float(event.get("reward", 0.0))
            experiences.append(
                {
                    "state": state_tensor,
                    "reward": reward,
                    "metadata": {
                        "timestamp": event.get("timestamp"),
                        "event_type": event.get("event_type", ""),
                        "session_id": event.get("session_id"),
                    },
                }
            )
        return experiences

    def _log_performance(self, experiences: List[Dict[str, Any]], telemetry: Sequence[Dict[str, Any]]) -> None:
        if self.current_intelligence is None:
            return
        rewards = [float(exp.get("reward", 0.0)) for exp in experiences]
        avg_reward = float(np.mean(rewards)) if rewards else 0.0
        positive = sum(1 for reward in rewards if reward > 0)
        win_rate = (positive / len(rewards)) if rewards else None

        roi_values = [
            float(event.get("trade", {}).get("roi"))
            for event in telemetry
            if isinstance(event.get("trade"), dict) and event.get("trade", {}).get("roi") is not None
        ]
        rolling_roi = float(np.mean(roi_values)) if roi_values else None
        drift_values = [
            float(event.get("drift_score"))
            for event in telemetry
            if event.get("drift_score") is not None
        ]
        drift_score = float(np.mean(drift_values)) if drift_values else None

        latency_ms = None
        if getattr(self.current_intelligence, "processing_latency", None) is not None:
            latency_ms = float(self.current_intelligence.processing_latency) * 1000.0

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "experience_count": len(experiences),
            "intelligence_latency_ms": latency_ms,
            "meta_confidence": np.mean(list(self.current_intelligence.meta_confidence_scores.values()))
            if self.current_intelligence.meta_confidence_scores
            else 0.0,
            "reward_avg": avg_reward,
            "win_rate": win_rate,
            "rolling_roi": rolling_roi,
            "drift_score": drift_score,
        }
        self._performance_history.append(record)
        if len(self._performance_history) > 500:
            self._performance_history = self._performance_history[-250:]

        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(timezone.utc),
            policy_version=str(self.config.get("policy_version", "unknown")),
            reward_avg=avg_reward,
            rolling_roi=rolling_roi,
            win_rate=win_rate,
            regret=None,
            latency_ms=latency_ms,
            experience_count=len(experiences),
            experience_buffer_size=self.experience_buffer.size(),
            drift_score=drift_score,
        )
        self.performance_tracker.record_snapshot(snapshot)
        if self.retrain_scheduler:
            self.retrain_scheduler.evaluate(snapshot)

    def _on_retrain_decision(self, decision, snapshot: PerformanceSnapshot) -> None:
        event = {
            "decision": {
                "reason": decision.reason,
                "timestamp": decision.timestamp.isoformat(),
            },
            "snapshot": snapshot.as_dict(),
        }
        self.retrain_events.append(event)
        logger.warning("Auto retrain scheduled", extra=event["decision"])

    # ------------------------------------------------------------------ #
    async def _collect_market_data(self) -> Dict[str, Any]:
        """
        Placeholder for data acquisition.
        Override this method to connect live feeds.
        """
        return {}

    async def _collect_telemetry(self) -> List[Dict[str, Any]]:
        """
        Placeholder for telemetry ingestion.
        Override to pull from queue or database.
        """
        return []

    # ------------------------------------------------------------------ #
    def stop(self) -> None:
        self.is_running = False

    @property
    def performance_history(self) -> List[Dict[str, Any]]:
        return self._performance_history

