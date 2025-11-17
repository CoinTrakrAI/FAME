import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest
import torch

from training.live_intelligence_trainer import LiveIntelligenceTrainer


class DummyTrainer(LiveIntelligenceTrainer):
    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self._market_counter = 0

    async def _collect_market_data(self) -> Dict[str, Any]:
        self._market_counter += 1
        prices = {
            "AAPL": [100, 101, 102, 103, 104, 105],
            "MSFT": [200, 201, 202, 203, 204, 205],
        }
        return {"prices": prices, "timestamp": datetime.now(timezone.utc).isoformat()}

    async def _collect_telemetry(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reward": 0.2,
                "event_type": "trading.execute_trade",
                "portfolio_state": {"current_value": 100000, "positions": {"AAPL": {"weight": 0.1}}},
            }
        ]


@pytest.fixture
def trainer_config() -> Dict[str, Any]:
    return {
        "training_interval": 0.1,
        "intelligence": {},
        "feature_engine": {},
        "multi_agent": {"state_dim": 512, "action_dim": 3},
    }


def test_training_cycle_runs(trainer_config: Dict[str, Any]) -> None:
    trainer = DummyTrainer(trainer_config)
    asyncio.run(trainer._training_cycle())
    assert trainer.current_intelligence is not None
    assert len(trainer.performance_history) == 1
    assert trainer.experience_buffer.size() >= 1


def test_experience_buffer_cap(trainer_config: Dict[str, Any]) -> None:
    trainer_config["experience_buffer"] = {"capacity": 2, "sample_size": 0}
    trainer = DummyTrainer(trainer_config)
    for _ in range(3):
        asyncio.run(trainer._training_cycle())
    assert trainer.experience_buffer.size() <= 2


def test_auto_retrain_scheduler_integrates(trainer_config: Dict[str, Any]) -> None:
    trainer_config["auto_retrain"] = {
        "reward_drop_threshold": 0.3,
        "win_rate_threshold": 0.9,  # force trigger
        "drift_threshold": 1.0,
        "min_buffer_size": 0,
        "cooldown_minutes": 1,
    }
    trainer = DummyTrainer(trainer_config)
    asyncio.run(trainer._training_cycle())
    assert trainer.retrain_events  # one event recorded

