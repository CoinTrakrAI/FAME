from pathlib import Path

from training.rewards import RewardEngine


def test_reward_engine_compute(tmp_path: Path):
    config_path = tmp_path / "reward.yaml"
    config_path.write_text(
        """
reward_components:
  explicit_feedback:
    positive: 2.0
    neutral: 0.0
    negative: -1.0
  trade_roi:
    scale: 0.5
    clip: 0.1
  response_latency_ms:
    fast_threshold: 1500
    fast_bonus: 0.3
    slow_penalty: -0.2
""",
        encoding="utf-8",
    )
    engine = RewardEngine.from_file(config_path)
    event = {
        "feedback_type": "explicit",
        "score": 0.9,
        "trade": {"roi": 0.05},
        "latency_ms": 1200,
        "confidence": 0.8,
    }
    reward = engine.compute(event)
    assert reward > 0.0

