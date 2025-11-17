"""Streaming queue consumer for online trainer."""

from __future__ import annotations

import asyncio
import logging

from training.context import TrainingContext
from training.pipelines.run_online_update import OnlinePolicyTrainer
from telemetry.queue import consume_events


logger = logging.getLogger(__name__)


async def _handle_event(trainer: OnlinePolicyTrainer, event: dict) -> None:
    await trainer.drain([event])


async def run_consumer(context: TrainingContext) -> None:
    trainer = OnlinePolicyTrainer(context)
    stop_event = asyncio.Event()

    async def handler(event: dict) -> None:
        await _handle_event(trainer, event)

    try:
        logger.info("Starting training queue consumer", extra={"run_id": context.run_id})
        await consume_events(handler, stop_event=stop_event)
    finally:
        stop_event.set()


def main() -> None:
    context = TrainingContext(run_id="queue_consumer")
    asyncio.run(run_consumer(context))


if __name__ == "__main__":
    main()

