from datetime import datetime, timezone, timedelta

from training.monitoring import PerformanceSnapshot
from training.scheduler import AutoRetrainScheduler, RetrainConfig


def make_snapshot(
    reward: float,
    win_rate: float,
    drift: float,
    buffer_size: int,
) -> PerformanceSnapshot:
    return PerformanceSnapshot(
        timestamp=datetime.now(timezone.utc),
        policy_version="v1",
        reward_avg=reward,
        rolling_roi=0.1,
        win_rate=win_rate,
        regret=0.0,
        latency_ms=200,
        experience_count=100,
        experience_buffer_size=buffer_size,
        drift_score=drift,
    )


def test_auto_retrain_triggers_and_respects_cooldown(monkeypatch):
    triggered = []

    def callback(decision, snapshot):
        triggered.append(decision.reason)

    scheduler = AutoRetrainScheduler(
        RetrainConfig(
            reward_drop_threshold=0.2,
            win_rate_threshold=0.5,
            drift_threshold=0.3,
            min_buffer_size=10,
            cooldown_minutes=30,
        ),
        callback=callback,
    )

    decision = scheduler.evaluate(make_snapshot(0.1, 0.4, 0.2, 50))
    assert decision is not None
    assert triggered

    # Should not trigger again due to cooldown
    decision2 = scheduler.evaluate(make_snapshot(0.1, 0.4, 0.2, 50))
    assert decision2 is None

