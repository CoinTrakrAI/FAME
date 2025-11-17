"""Transform raw feedback into feature datasets."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from analytics.feature_store import FeatureStore
from training.context import TrainingContext
from training.pipelines.collect_feedback import _load_jsonl


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FeatureSetBuilder:
    """Build curated feature records for offline/online training."""

    context: TrainingContext
    feature_store: FeatureStore = field(default_factory=FeatureStore)

    def load_feedback(self, feedback_path: Path) -> List[Dict]:
        if not feedback_path.exists():
            logger.error("Feedback path missing", extra={"path": str(feedback_path)})
            return []
        return list(_load_jsonl(feedback_path))

    def build_records(self, feedback: Iterable[Dict]) -> List[Dict]:
        records: List[Dict] = []
        for event in feedback:
            record = {
                "run_id": self.context.run_id,
                "session_id": event.get("session_id"),
                "timestamp": event.get("timestamp"),
                "intent": event.get("intent"),
                "skill": event.get("skill"),
                "feedback_type": event.get("feedback_type"),
                "feedback_score": event.get("score"),
                "trade_symbol": event.get("trade", {}).get("symbol"),
                "trade_roi": event.get("trade", {}).get("roi"),
                "preferences_hash": event.get("preferences", {}).get("integrity_hash"),
                "latency_ms": event.get("latency_ms"),
                "response_confidence": event.get("confidence"),
            }
            records.append(record)
        logger.info("Constructed feature records", extra={"run_id": self.context.run_id, "count": len(records)})
        return records

    def run(self, feedback_path: Path) -> Optional[Path]:
        feedback = self.load_feedback(feedback_path)
        if not feedback:
            return None
        records = self.build_records(feedback)
        return self.feature_store.save_dataset(self.context.run_id, records)

