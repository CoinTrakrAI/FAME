from monitoring.log_aggregator import LogAggregator


def test_log_aggregator_buffers_events():
    agg = LogAggregator(max_events=5)
    agg.emit("info", "test event", symbol="AAPL", value=1)
    assert agg.recent(1)[0]["message"] == "test event"
    assert agg.recent(1)[0]["fields"]["symbol"] == "AAPL"
    assert '"events"' in agg.to_json(limit=2)

