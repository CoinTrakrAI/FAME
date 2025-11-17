"""Collect raw feedback and telemetry events for training."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from training.context import TrainingContext


logger = logging.getLogger(__name__)


def _load_jsonl(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Skipping malformed feedback line", extra={"path": str(path)})


@dataclass(slots=True)
class FeedbackCollector:
    """Aggregate and deduplicate feedback/telemetry events."""

    context: TrainingContext
    sources: Sequence[Path] = field(default_factory=lambda: [Path("telemetry/feedback")])
    output_dir: Path = Path("data/training/feedback")

    def __post_init__(self) -> None:
        self.sources = [Path(src) for src in self.sources]
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect(self) -> List[Dict]:
        events: Dict[Tuple[str, str], Dict] = {}
        for source in self.sources:
            if not source.exists():
                logger.debug("Feedback source missing", extra={"path": str(source)})
                continue
            for file in source.glob("*.jsonl"):
                for record in _load_jsonl(file):
                    session_id = record.get("session_id", "unknown")
                    timestamp = record.get("timestamp")
                    if not timestamp:
                        continue
                    key = (session_id, timestamp)
                    events[key] = record
        logger.info("Collected feedback events", extra={"run_id": self.context.run_id, "count": len(events)})
        return list(events.values())

    def write(self, events: Iterable[Dict]) -> Optional[Path]:
        events = list(events)
        if not events:
            logger.warning("No feedback events collected", extra={"run_id": self.context.run_id})
            return None
        output_path = self.output_dir / f"feedback_{self.context.run_id}.jsonl"
        with output_path.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, ensure_ascii=False))
                handle.write("\n")
        return output_path

    def run(self) -> Optional[Path]:
        events = self.collect()
        return self.write(events)

