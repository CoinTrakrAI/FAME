"""Feature store utilities for training pipelines."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class FeatureStore:
    """Simple JSONL-backed feature store for offline/online training."""

    root: Path = Path("data/feature_store")

    def __post_init__(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def dataset_path(self, run_id: str) -> Path:
        return self.root / f"features_{run_id}.jsonl"

    def save_dataset(self, run_id: str, records: Iterable[Dict]) -> Path:
        path = self.dataset_path(run_id)
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False))
                handle.write("\n")
        logger.info("Feature dataset saved", extra={"run_id": run_id, "path": str(path)})
        return path

    def load_dataset(self, run_id: str) -> List[Dict]:
        path = self.dataset_path(run_id)
        if not path.exists():
            logger.warning("Feature dataset not found", extra={"run_id": run_id, "path": str(path)})
            return []
        with path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def list_datasets(self) -> List[str]:
        return sorted(p.stem.replace("features_", "") for p in self.root.glob("features_*.jsonl"))


