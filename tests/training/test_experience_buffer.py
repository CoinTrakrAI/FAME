import math
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import torch

from training.replay.experience_buffer import ExperienceBuffer


def _make_experience(value: float, ts: datetime | None = None):
    metadata = {"timestamp": ts.isoformat() if ts else datetime.now(timezone.utc).isoformat()}
    return {
        "state": torch.tensor([value], dtype=torch.float32),
        "reward": value,
        "metadata": metadata,
    }


def test_experience_buffer_priority_and_capacity(tmp_path: Path):
    buffer = ExperienceBuffer(capacity=3)
    for reward in [0.1, 0.5, -0.3, 0.9]:
        buffer.add(_make_experience(reward))
    assert buffer.size() == 3
    sampled = buffer.sample(2)
    assert len(sampled) == 2


def test_experience_buffer_ttl(tmp_path: Path):
    buffer = ExperienceBuffer(capacity=5, ttl_seconds=1)
    old_ts = datetime.now(timezone.utc) - timedelta(seconds=5)
    buffer.add(_make_experience(0.1, ts=old_ts))
    buffer.add(_make_experience(0.2))
    # sample triggers TTL cleanup
    buffer.sample(1)
    assert buffer.size() == 1


def test_experience_buffer_persistence(tmp_path: Path):
    snapshot = tmp_path / "snapshot.jsonl"
    buffer = ExperienceBuffer(capacity=5, persistence_path=snapshot)
    buffer.add(_make_experience(0.4))
    buffer.save_snapshot()
    new_buffer = ExperienceBuffer(capacity=5, persistence_path=snapshot)
    assert math.isclose(new_buffer.sample(1)[0]["reward"], 0.4, rel_tol=1e-3)

