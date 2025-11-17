import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from analytics.feature_store import FeatureStore
from training.pipelines.historical_ingest import (
    HistoricalIngestConfig,
    HistoricalIngestPipeline,
)


def _write_event_file(tmp_dir: Path, name: str, events) -> None:
    path = tmp_dir / name
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event))
            handle.write("\n")


def test_historical_ingest_builds_dataset(tmp_path):
    telemetry_dir = tmp_path / "telemetry"
    telemetry_dir.mkdir()

    now = datetime.now(timezone.utc)
    events = [
        {
            "timestamp": now.isoformat(),
            "session_id": "session-1",
            "intent": "trading.get_signal",
            "skill": "trading_skill",
            "source": "voice",
            "latency_ms": 320,
            "confidence": 0.82,
            "score": 0.7,
            "feedback_type": "explicit",
            "task_success": True,
            "trade": {"roi": 0.05, "notional": 10000, "slippage_bps": 3},
        },
        {
            "timestamp": (now - timedelta(days=10)).isoformat(),
            "session_id": "session-2",
            "intent": "qa_engine",
            "confidence": 0.2,
            "score": 0.1,
            "feedback_type": "implicit",
        },
    ]
    _write_event_file(telemetry_dir, "events_test.jsonl", events)

    feature_store = FeatureStore(root=tmp_path / "feature_store")
    config = HistoricalIngestConfig(telemetry_dir=telemetry_dir, max_days=30, min_confidence=0.3)
    pipeline = HistoricalIngestPipeline(feature_store, config)

    dataset_path = pipeline.run("unit_test")
    assert dataset_path.exists()

    with dataset_path.open("r", encoding="utf-8") as handle:
        lines = [json.loads(line) for line in handle]

    # Only first event should pass confidence threshold
    assert len(lines) == 1
    record = lines[0]
    assert record["features"]["intent"] == "trading.get_signal"
    assert record["features"]["trade_roi"] == 0.05
    assert record["targets"]["explicit_feedback"] is True
    assert record["targets"]["task_success"] is True

