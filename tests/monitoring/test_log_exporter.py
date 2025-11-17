import json
from datetime import datetime, timezone

import pytest

from monitoring import log_exporter as log_exporter_module
from monitoring.log_aggregator import LogAggregator
from monitoring.log_exporter import LogExporter, LogExporterConfig


class DummyResponse:
    def __init__(self, status_code: int = 200, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


@pytest.mark.skipif(log_exporter_module.requests is None, reason="requests library not available")
def test_log_exporter_sends_to_elastic(monkeypatch):
    aggregator = LogAggregator(max_events=10)
    aggregator.emit_json(
        {"message": "test", "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    config = LogExporterConfig(
        batch_size=5, elastic_url="http://elastic:9200", elastic_index="fame-test"
    )
    exporter = LogExporter(aggregator, config)

    calls = []

    def fake_post(url, data=None, headers=None, timeout=10):
        calls.append((url, data, headers))
        return DummyResponse()

    monkeypatch.setattr("monitoring.log_exporter.requests.post", fake_post)

    exported = exporter._export_batch()

    assert exported == 1
    assert calls
    assert calls[0][0].endswith("/_bulk")
    lines = calls[0][1].strip().split("\n")
    assert json.loads(lines[1])["message"] == "test"

