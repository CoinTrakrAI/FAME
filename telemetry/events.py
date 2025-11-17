"""Training telemetry event emission helpers."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

EVENT_SINK = Path("telemetry/feedback")
EVENT_SINK.mkdir(parents=True, exist_ok=True)

try:
    from telemetry.queue import enqueue_event
except ImportError:  # pragma: no cover - optional dependency
    enqueue_event = None

try:
    from monitoring.ingest_pipeline import IngestPipeline
except ImportError:  # pragma: no cover - optional dependency
    IngestPipeline = None  # type: ignore

_INGEST_PIPELINE: Optional["IngestPipeline"] = None


def register_ingest_pipeline(pipeline: "IngestPipeline") -> None:
    global _INGEST_PIPELINE
    _INGEST_PIPELINE = pipeline


def _submit_to_ingest(payload: Dict[str, Any]) -> None:
    if _INGEST_PIPELINE is None:
        return
    try:
        submitted = _INGEST_PIPELINE.submit_nowait(payload.copy())
        if not submitted:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(_INGEST_PIPELINE.submit(payload.copy()))
    except RuntimeError:
        # No running loop; ignore
        pass
    except Exception:  # pragma: no cover - defensive path
        logger.debug("Failed to push event to ingest pipeline", exc_info=True)


def emit_training_event(payload: Dict[str, Any], sink: Optional[Path] = None) -> None:
    """Emit a training telemetry event to JSONL sink."""

    try:
        sink_path = sink or EVENT_SINK
        sink_path.mkdir(parents=True, exist_ok=True)

        if "timestamp" not in payload:
            payload["timestamp"] = datetime.now(timezone.utc).isoformat()

        if "session_id" not in payload:
            logger.warning("Training event missing session_id", extra={"payload_keys": list(payload.keys())})
            payload["session_id"] = "unknown"

        log_file = sink_path / f"events_{datetime.now(timezone.utc):%Y%m%d}.jsonl"
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False))
            handle.write("\n")

        logger.debug(
            "Emitted training event",
            extra={
                "session_id": payload["session_id"],
                "intent": payload.get("intent"),
                "file": log_file.name,
            },
        )
        if enqueue_event:
            enqueue_event(payload)
        _submit_to_ingest(payload)
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(
            "Failed to emit training event",
            extra={"error": str(exc), "payload_keys": list(payload.keys())},
        )
