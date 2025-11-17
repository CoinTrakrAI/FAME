"""
Monitoring ingest pipeline for normalising telemetry events before metrics/log export.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IngestedEvent:
    timestamp: datetime
    source: str
    category: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "category": self.category,
            "metadata": self.metadata,
            "metrics": self.metrics,
            "tags": self.tags,
        }


class IngestPipeline:
    """
    Normalise heterogeneous telemetry events so they can be exported to metrics, traces, or log sinks.
    """

    def __init__(self) -> None:
        self._processors: List["EventProcessor"] = []
        self._queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1024)
        self._shutdown = asyncio.Event()
        self._task: Optional[asyncio.Task[None]] = None

    def register_processor(self, processor: "EventProcessor") -> None:
        self._processors.append(processor)

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run(), name="monitoring_ingest_pipeline")

    async def stop(self) -> None:
        self._shutdown.set()
        if self._task:
            await self._task
            self._task = None

    async def submit(self, event: Dict[str, Any]) -> None:
        try:
            await self._queue.put(event)
        except asyncio.QueueFull:
            logger.warning("Ingest pipeline queue full; dropping event from %s", event.get("source", "unknown"))

    def submit_nowait(self, event: Dict[str, Any]) -> bool:
        try:
            self._queue.put_nowait(event)
            return True
        except asyncio.QueueFull:
            logger.warning("Ingest pipeline queue full; dropping event from %s", event.get("source", "unknown"))
        except RuntimeError:
            # Queue not initialised or already closed
            logger.debug("Ingest pipeline queue unavailable for submit_nowait")
        return False

    async def _run(self) -> None:
        while not self._shutdown.is_set():
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            try:
                ingested = self._normalise(event)
                if ingested is None:
                    continue
                await self._dispatch(ingested)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Failed to normalise event: %s", exc)

    def _normalise(self, event: Dict[str, Any]) -> Optional[IngestedEvent]:
        timestamp = event.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp_obj = datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp_obj = datetime.now(timezone.utc)
        elif isinstance(timestamp, datetime):
            timestamp_obj = timestamp.astimezone(timezone.utc)
        else:
            timestamp_obj = datetime.now(timezone.utc)

        source = str(event.get("source") or event.get("skill") or "unknown")
        category = str(event.get("category") or "general")
        metadata = dict(event.get("metadata") or {})

        tags = self._derive_tags(event)
        metrics = self._extract_metrics(event)

        return IngestedEvent(
            timestamp=timestamp_obj,
            source=source,
            category=category,
            metadata=metadata,
            metrics=metrics,
            tags=tags,
        )

    def _derive_tags(self, event: Dict[str, Any]) -> Dict[str, str]:
        tags: Dict[str, str] = {}
        session_id = event.get("session_id")
        if session_id:
            tags["session_id"] = str(session_id)
        tenant = event.get("tenant") or event.get("customer_id")
        if tenant:
            tags["tenant"] = str(tenant)
        strategy = event.get("strategy") or event.get("strategy_name")
        if strategy:
            tags["strategy"] = str(strategy)
        intent = event.get("intent") or event.get("category")
        if intent:
            tags["intent"] = str(intent)
        channel = event.get("source") or event.get("channel")
        if channel:
            tags["channel"] = str(channel)
        return tags

    def _extract_metrics(self, event: Dict[str, Any]) -> Dict[str, float]:
        metrics: Dict[str, float] = {}
        for key in ("confidence", "score", "latency_ms", "roi", "projected_roi", "win_rate"):
            value = event.get(key)
            if isinstance(value, (int, float)):
                metrics[key] = float(value)

        trade = event.get("trade") or {}
        if isinstance(trade, dict):
            for key in ("notional", "slippage_bps", "fill_rate", "latency_ms"):
                value = trade.get(key)
                if isinstance(value, (int, float)):
                    metrics[f"trade_{key}"] = float(value)

        voice = event.get("voice") or {}
        if isinstance(voice, dict):
            latency = voice.get("latency_ms")
            if isinstance(latency, (int, float)):
                metrics["voice_latency_ms"] = float(latency)
            success = voice.get("success_rate")
            if isinstance(success, (int, float)):
                metrics["voice_success_rate"] = float(success)

        risk = event.get("risk") or {}
        if isinstance(risk, dict):
            for key in ("stress_market_crash", "liquidity_pressure", "var_95", "cvar_95"):
                value = risk.get(key)
                if isinstance(value, (int, float)):
                    metrics[f"risk_{key}"] = float(value)

        return metrics

    async def _dispatch(self, event: IngestedEvent) -> None:
        if not self._processors:
            logger.debug("No processors registered for ingest pipeline")
            return
        await asyncio.gather(*(processor.process(event) for processor in self._processors), return_exceptions=True)


class EventProcessor:
    async def process(self, event: IngestedEvent) -> None:
        raise NotImplementedError


