import asyncio
from datetime import datetime, timezone

from monitoring.ingest_pipeline import EventProcessor, IngestPipeline


class DummyProcessor(EventProcessor):
    def __init__(self) -> None:
        self.events = []

    async def process(self, event) -> None:
        self.events.append(event)


def test_ingest_pipeline_normalises_event():
    asyncio.run(_run_normalisation())


async def _run_normalisation() -> None:
    pipeline = IngestPipeline()
    processor = DummyProcessor()
    pipeline.register_processor(processor)

    await pipeline.start()
    try:
        await pipeline.submit(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "trading_service",
                "category": "trade_execution",
                "session_id": "session-123",
                "tenant": "alpha",
                "trade": {"notional": 100000, "slippage_bps": 5},
            }
        )
        await asyncio.sleep(0.1)
    finally:
        await pipeline.stop()

    assert processor.events
    event = processor.events[0]
    assert event.source == "trading_service"
    assert event.tags["tenant"] == "alpha"
    assert event.metrics["trade_notional"] == 100000
    assert event.metrics["trade_slippage_bps"] == 5


def test_ingest_pipeline_handles_missing_timestamp():
    asyncio.run(_run_missing_timestamp())


async def _run_missing_timestamp() -> None:
    pipeline = IngestPipeline()
    processor = DummyProcessor()
    pipeline.register_processor(processor)

    await pipeline.start()
    try:
        await pipeline.submit({"source": "qa_engine"})
        await asyncio.sleep(0.1)
    finally:
        await pipeline.stop()

    assert processor.events
    event = processor.events[0]
    assert event.source == "qa_engine"
    assert isinstance(event.timestamp, datetime)
    assert event.timestamp.tzinfo is not None

