from datetime import datetime, timezone

from training.monitoring import PerformanceSnapshot, TrainingPerformanceTracker


def test_performance_tracker_records_snapshots():
    tracker = TrainingPerformanceTracker()
    snapshot = PerformanceSnapshot(
        timestamp=datetime.now(timezone.utc),
        policy_version="v1",
        reward_avg=0.75,
        rolling_roi=0.12,
        win_rate=0.6,
        regret=0.1,
        latency_ms=120.0,
        experience_count=50,
        experience_buffer_size=200,
        drift_score=0.02,
    )

    tracker.record_snapshot(snapshot)
    recent = tracker.recent_snapshots(limit=1)

    assert len(recent) == 1
    assert recent[0]["policy_version"] == "v1"
    assert recent[0]["reward_avg"] == 0.75

