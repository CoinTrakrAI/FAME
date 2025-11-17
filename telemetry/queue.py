"""Streaming queue utilities for training telemetry."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from queue import Queue, Empty
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError:  # pragma: no cover - optional dependency
    AIOKafkaConsumer = None  # type: ignore[assignment]
    AIOKafkaProducer = None  # type: ignore[assignment]


TrainingEventHandler = Callable[[Dict[str, Any]], Awaitable[None]]
_IN_MEMORY_QUEUE: Queue = Queue()


def enqueue_event(event: Dict[str, Any]) -> None:
    """Put event into the in-memory queue (non-blocking)."""
    try:
        _IN_MEMORY_QUEUE.put_nowait(event)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("Failed to enqueue training event", extra={"error": str(exc)})


async def consume_events(handler: TrainingEventHandler, stop_event: Optional[asyncio.Event] = None) -> None:
    """Consume events from queue (Kafka if configured, otherwise in-memory)."""
    queue_settings = _QueueSettings.from_env()
    if queue_settings.use_kafka():
        if AIOKafkaConsumer is None:
            logger.warning("Kafka requested but aiokafka not installed; falling back to in-memory queue")
        else:
            await _consume_kafka(queue_settings, handler, stop_event)
            return
    await _consume_in_memory(handler, stop_event)


async def publish_event_async(event: Dict[str, Any]) -> None:
    """Publish event to Kafka if configured and library is available."""
    queue_settings = _QueueSettings.from_env()
    if not queue_settings.use_kafka() or AIOKafkaProducer is None:
        return
    producer = AIOKafkaProducer(
        bootstrap_servers=queue_settings.brokers,
        client_id=queue_settings.client_id,
    )
    await producer.start()
    try:
        payload = json.dumps(event, ensure_ascii=False).encode("utf-8")
        await producer.send_and_wait(queue_settings.topic, payload)
    finally:
        await producer.stop()


async def _consume_in_memory(handler: TrainingEventHandler, stop_event: Optional[asyncio.Event]) -> None:
    loop = asyncio.get_running_loop()
    while True:
        if stop_event and stop_event.is_set():
            break
        event = await loop.run_in_executor(None, _blocking_get)
        if event is None:
            break
        await handler(event)


async def _consume_kafka(settings: "_QueueSettings", handler: TrainingEventHandler, stop_event: Optional[asyncio.Event]) -> None:
    consumer = AIOKafkaConsumer(
        settings.topic,
        bootstrap_servers=settings.brokers,
        group_id=settings.group_id,
        client_id=settings.client_id,
        enable_auto_commit=True,
        auto_offset_reset="latest",
    )
    await consumer.start()
    try:
        async for msg in consumer:
            if stop_event and stop_event.is_set():
                break
            try:
                event = json.loads(msg.value)
                if isinstance(event, dict):
                    await handler(event)
            except json.JSONDecodeError:
                logger.warning("Discarded malformed kafka event")
    finally:
        await consumer.stop()


def _blocking_get(timeout: float = 0.5) -> Optional[Dict[str, Any]]:
    try:
        return _IN_MEMORY_QUEUE.get(timeout=timeout)
    except Empty:
        return None


@dataclass(slots=True)
class _QueueSettings:
    brokers: Optional[str]
    topic: str = "training-telemetry"
    group_id: str = "training-consumer"
    client_id: str = "training-client"

    @classmethod
    def from_env(cls) -> "_QueueSettings":
        return cls(
            brokers=os.getenv("TRAINING_QUEUE_BROKERS"),
            topic=os.getenv("TRAINING_QUEUE_TOPIC", "training-telemetry"),
            group_id=os.getenv("TRAINING_QUEUE_GROUP", "training-consumer"),
            client_id=os.getenv("TRAINING_QUEUE_CLIENT", "training-client"),
        )

    def use_kafka(self) -> bool:
        return bool(self.brokers)

