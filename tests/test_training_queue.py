import asyncio

from telemetry.queue import consume_events, enqueue_event


def test_in_memory_queue_consumption():
    captured = []

    async def main():
        stop_event = asyncio.Event()

        async def handler(event):
            captured.append(event)
            stop_event.set()

        consumer_task = asyncio.create_task(consume_events(handler, stop_event=stop_event))
        enqueue_event({"session_id": "q1"})
        await asyncio.wait_for(stop_event.wait(), timeout=1.0)
        await consumer_task

    asyncio.run(main())
    assert captured and captured[0]["session_id"] == "q1"

