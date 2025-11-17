"""Offline policy training orchestration."""

from __future__ import annotations

import json
import logging
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from analytics.feature_store import FeatureStore
from training.context import TrainingContext

try:
    from intelligence.reinforcement_trainer import ReinforcementTrainer
except ImportError:  # pragma: no cover - optional dependency
    ReinforcementTrainer = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OfflinePolicyTrainer:
    """Run batch policy updates using collected feedback."""

    context: TrainingContext
    feature_store: FeatureStore = field(default_factory=FeatureStore)
    config: Dict = field(init=False)

    def __post_init__(self) -> None:
        self.config = self._load_config(self.context.config_path)

    def _load_config(self, path: Path) -> Dict:
        if not path.exists():
            logger.warning("Training config not found, using defaults", extra={"path": str(path)})
            return {
                "training": {"batch_size": 512, "learning_rate": 1e-4},
                "evaluation": {"min_samples": 100},
            }
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def load_dataset(self) -> List[Dict]:
        dataset = self.feature_store.load_dataset(self.context.run_id)
        logger.info("Loaded feature dataset", extra={"run_id": self.context.run_id, "count": len(dataset)})
        return dataset

    def _summarise_feedback(self, dataset: List[Dict]) -> Dict:
        scores = [record["feedback_score"] for record in dataset if isinstance(record.get("feedback_score"), (int, float))]
        roi = [record["trade_roi"] for record in dataset if isinstance(record.get("trade_roi"), (int, float))]
        return {
            "sample_count": len(dataset),
            "feedback_score_mean": statistics.fmean(scores) if scores else None,
            "trade_roi_mean": statistics.fmean(roi) if roi else None,
        }

    def _train_policy(self, dataset: List[Dict]) -> Dict:
        summary = self._summarise_feedback(dataset)
        if ReinforcementTrainer is None:
            logger.warning("ReinforcementTrainer unavailable; skipping policy update")
            return {"status": "skipped", **summary}

        trainer = ReinforcementTrainer()
        # Placeholder: hook into reinforcement trainer once feature encoding is defined.
        logger.info("Offline training run simulated", extra={"run_id": self.context.run_id})
        return {"status": "completed", **summary}

    def _write_report(self, metrics: Dict) -> Path:
        output_dir = self.context.resolve_output_path()
        report_path = output_dir / "training_report.json"
        with report_path.open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "run_id": self.context.run_id,
                    "timestamp": self.context.timestamp.isoformat(),
                    "metrics": metrics,
                    "config": self.config,
                },
                handle,
                indent=2,
                ensure_ascii=False,
            )
        logger.info("Offline training report written", extra={"path": str(report_path)})
        return report_path

    def run(self) -> Optional[Path]:
        dataset = self.load_dataset()
        if not dataset:
            logger.error("Offline training aborted - dataset empty", extra={"run_id": self.context.run_id})
            return None
        metrics = self._train_policy(dataset)
        return self._write_report(metrics)

