"""
Prioritised experience replay buffer with optional persistence.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:  # Optional torch dependency for tensor conversion
    import torch
except ImportError:  # pragma: no cover
    torch = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExperienceRecord:
    data: Dict[str, Any]
    priority: float
    timestamp: datetime

    def serialise(self) -> Dict[str, Any]:
        record = dict(self.data)
        state = record.get("state")
        if torch is not None and isinstance(state, torch.Tensor):
            record["state"] = state.detach().cpu().tolist()
            record["_state_shape"] = list(state.shape)
        return {
            "data": record,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
        }

    @staticmethod
    def deserialise(payload: Dict[str, Any]) -> "ExperienceRecord":
        data = dict(payload["data"])
        state = data.get("state")
        shape = data.pop("_state_shape", None)
        if torch is not None and state is not None and shape is not None:
            data["state"] = torch.tensor(state).view(*shape)
        ts = datetime.fromisoformat(payload["timestamp"])
        return ExperienceRecord(
            data=data,
            priority=float(payload["priority"]),
            timestamp=ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc),
        )


class ExperienceBuffer:
    """
    Experience replay buffer with priority sampling, TTL, and snapshot support.
    """

    def __init__(
        self,
        capacity: int = 10_000,
        ttl_seconds: Optional[int] = None,
        persistence_path: Optional[Path | str] = None,
    ) -> None:
        self.capacity = max(1, capacity)
        self.ttl_seconds = ttl_seconds
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self._records: List[ExperienceRecord] = []

        if self.persistence_path and self.persistence_path.exists():
            try:
                self.load_snapshot(self.persistence_path)
            except Exception as exc:  # pragma: no cover - defensive load
                logger.warning("Failed to load experience snapshot: %s", exc)

    # ------------------------------------------------------------------ #
    def add(self, experience: Dict[str, Any], priority: Optional[float] = None) -> None:
        record = self._create_record(experience, priority)
        self._records.append(record)
        self._apply_ttl()
        self._truncate()

    def add_many(self, experiences: Iterable[Dict[str, Any]]) -> None:
        for exp in experiences:
            self.add(exp)

    def sample(self, batch_size: int, weighted: bool = True) -> List[Dict[str, Any]]:
        self._apply_ttl()
        if not self._records:
            return []
        batch_size = max(1, min(batch_size, len(self._records)))
        if weighted:
            weights = [max(rec.priority, 1e-9) for rec in self._records]
            indices = random.choices(range(len(self._records)), weights=weights, k=batch_size)
        else:
            indices = random.sample(range(len(self._records)), batch_size)
        return [self._records[i].data for i in indices]

    def size(self) -> int:
        self._apply_ttl()
        return len(self._records)

    def save_snapshot(self, path: Optional[Path | str] = None) -> Path:
        target = Path(path) if path else self.persistence_path
        if target is None:
            raise ValueError("No snapshot path configured for experience buffer.")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            for record in self._records:
                handle.write(json.dumps(record.serialise(), ensure_ascii=False))
                handle.write("\n")
        logger.info("Experience buffer snapshot saved", extra={"path": str(target), "records": len(self._records)})
        return target

    def load_snapshot(self, path: Path | str) -> None:
        target = Path(path)
        if not target.exists():
            logger.warning("Experience snapshot not found", extra={"path": str(target)})
            return
        records: List[ExperienceRecord] = []
        with target.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                records.append(ExperienceRecord.deserialise(payload))
        self._records = records[-self.capacity :]
        logger.info("Experience buffer snapshot loaded", extra={"path": str(target), "records": len(self._records)})

    # ------------------------------------------------------------------ #
    def _create_record(self, experience: Dict[str, Any], priority: Optional[float]) -> ExperienceRecord:
        ts_val = experience.get("metadata", {}).get("timestamp")
        timestamp = _parse_timestamp(ts_val) or datetime.now(timezone.utc)
        reward = experience.get("reward")
        computed_priority = priority
        if computed_priority is None:
            try:
                computed_priority = abs(float(reward)) + 1e-6
            except (TypeError, ValueError):
                computed_priority = 1e-6
        return ExperienceRecord(data=dict(experience), priority=float(computed_priority), timestamp=timestamp)

    def _apply_ttl(self) -> None:
        if self.ttl_seconds is None:
            return
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.ttl_seconds)
        if self._records and self._records[0].timestamp < cutoff:
            self._records = [rec for rec in self._records if rec.timestamp >= cutoff]

    def _truncate(self) -> None:
        if len(self._records) <= self.capacity:
            return
        # Keep highest priority; tie-breaker by recency
        self._records.sort(key=lambda rec: (rec.priority, rec.timestamp), reverse=True)
        self._records = self._records[: self.capacity]


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return None

