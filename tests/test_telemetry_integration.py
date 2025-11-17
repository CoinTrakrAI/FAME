from datetime import datetime, timezone
import json

from telemetry.events import emit_training_event, register_ingest_pipeline


def test_telemetry_emission(tmp_path):
    """Events should be appended to JSONL sink with required fields."""
    test_sink = tmp_path / "telemetry_test"
    event = {
        "session_id": "test_session_123",
        "intent": "buy_stock",
        "skill": "trading",
        "feedback_type": "test",
        "score": 0.8,
    }

    emit_training_event(event, sink=test_sink)

    expected_file = test_sink / f"events_{datetime.now(timezone.utc):%Y%m%d}.jsonl"
    assert expected_file.exists()

    with expected_file.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()
    assert len(lines) == 1
    written_event = json.loads(lines[0])
    assert written_event["session_id"] == "test_session_123"
    assert "timestamp" in written_event


def test_ingest_pipeline_registration(monkeypatch):
    captured = {}

    class DummyPipeline:
        def submit_nowait(self, event):
            captured["event"] = event
            return True

    register_ingest_pipeline(DummyPipeline())

    emit_training_event({"session_id": "abc", "intent": "hello"}, sink=None)

    assert captured["event"]["intent"] == "hello"

