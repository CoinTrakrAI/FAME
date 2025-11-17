"""
Historical data ingestion pipeline for training.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from analytics.feature_store import FeatureStore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class HistoricalExample:
    features: Dict[str, Any]
    targets: Dict[str, Any]
    metadata: Dict[str, Any]

    def as_record(self) -> Dict[str, Any]:
        return {
            "features": self.features,
            "targets": self.targets,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class HistoricalIngestConfig:
    telemetry_dir: Path = Path("telemetry/feedback")
    max_days: Optional[int] = 90
    min_confidence: float = 0.0
    include_trade_records: bool = True


class HistoricalIngestPipeline:
    """
    Build feature datasets from historical telemetry events and trading outcomes.
    """

    def __init__(
        self,
        feature_store: Optional[FeatureStore] = None,
        config: Optional[HistoricalIngestConfig] = None,
    ) -> None:
        self.feature_store = feature_store or FeatureStore()
        self.config = config or HistoricalIngestConfig()

    def run(self, run_id: str) -> Path:
        logger.info("Starting historical ingest", extra={"run_id": run_id})
        examples = list(self._collect_examples())
        if not examples:
            logger.warning("Historical ingest produced no examples", extra={"run_id": run_id})
            return self.feature_store.save_dataset(run_id, [])

        records = [example.as_record() for example in examples]
        path = self.feature_store.save_dataset(run_id, records)
        logger.info(
            "Historical ingest completed",
            extra={"run_id": run_id, "records": len(records), "path": str(path)},
        )
        return path

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _collect_examples(self) -> Iterable[HistoricalExample]:
        cutoff = None
        if self.config.max_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=self.config.max_days)

        for event in self._iter_telemetry_events():
            event_ts = _parse_timestamp(event.get("timestamp"))
            if cutoff and event_ts and event_ts < cutoff:
                continue

            if self.config.min_confidence:
                confidence = _safe_float(event.get("confidence"))
                if confidence is not None and confidence < self.config.min_confidence:
                    continue

            example = self._build_example(event, event_ts)
            if example:
                yield example

    def _iter_telemetry_events(self) -> Iterable[Dict[str, Any]]:
        telemetry_dir = self.config.telemetry_dir
        if not telemetry_dir.exists():
            logger.warning("Telemetry directory missing", extra={"path": str(telemetry_dir)})
            return []

        for path in sorted(telemetry_dir.glob("events_*.jsonl")):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            yield json.loads(line)
                        except json.JSONDecodeError:
                            logger.debug("Skipping malformed telemetry line", extra={"path": str(path)})
            except OSError as exc:  # pragma: no cover - IO error
                logger.error("Failed to read telemetry file", extra={"path": str(path), "error": str(exc)})

    def _build_example(
        self,
        event: Dict[str, Any],
        timestamp: Optional[datetime],
    ) -> Optional[HistoricalExample]:
        features: Dict[str, Any] = {
            "intent": event.get("intent") or event.get("category"),
            "skill": event.get("skill") or event.get("source"),
            "channel": event.get("source"),
            "latency_ms": _safe_float(event.get("latency_ms")),
            "confidence": _safe_float(event.get("confidence")),
            "score": _safe_float(event.get("score")),
            "reward": _safe_float(event.get("reward")),
        }

        voice = event.get("voice") or {}
        if isinstance(voice, dict):
            features["voice_latency_ms"] = _safe_float(voice.get("latency_ms"))
            features["voice_success_rate"] = _safe_float(voice.get("success_rate"))

        trade = event.get("trade") or {}
        if isinstance(trade, dict) and self.config.include_trade_records:
            features["trade_roi"] = _safe_float(trade.get("roi"))
            features["trade_notional"] = _safe_float(trade.get("notional"))
            features["trade_slippage_bps"] = _safe_float(trade.get("slippage_bps"))
            features["trade_fill_rate"] = _safe_float(trade.get("fill_rate"))

        targets: Dict[str, Any] = {
            "reward": _safe_float(event.get("reward") or event.get("score")),
            "explicit_feedback": bool(
                (event.get("feedback_type") or "").lower() == "explicit"
            ),
            "task_success": bool(
                event.get("task_success")
                or (event.get("context") or {}).get("task_success")
            ),
        }

        metadata: Dict[str, Any] = {
            "timestamp": (timestamp or datetime.now(timezone.utc)).isoformat(),
            "session_id": event.get("session_id"),
            "policy_version": event.get("policy_version"),
            "event_type": event.get("type") or "telemetry",
        }

        features = _clean_dict(features)
        targets = _clean_dict(targets)

        if not features or not targets:
            return None
        return HistoricalExample(features=features, targets=targets, metadata=_clean_dict(metadata))


# ---------------------------------------------------------------------- #
# Utility helpers
# ---------------------------------------------------------------------- #


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            # datetime.fromisoformat handles timezone suffixes in py3.11+
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None
    return None


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}

