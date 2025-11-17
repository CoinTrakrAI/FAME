"""Shared training context utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


@dataclass(slots=True)
class TrainingContext:
    """Runtime context for training pipelines."""

    run_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    config_path: Path = field(default_factory=lambda: Path("training/configs/training_config.yaml"))
    reward_schema_path: Path = field(default_factory=lambda: Path("training/configs/reward_schema.yaml"))
    metadata: Dict[str, str] = field(default_factory=dict)
    output_dir: Path = field(default_factory=lambda: Path("models/policies"))

    def resolve_output_path(self) -> Path:
        """Return directory for the current run."""
        path = self.output_dir / self.run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def with_metadata(self, **kwargs: str) -> "TrainingContext":
        """Return a shallow copy with additional metadata."""
        updated = dict(self.metadata)
        updated.update(kwargs)
        return TrainingContext(
            run_id=self.run_id,
            timestamp=self.timestamp,
            config_path=self.config_path,
            reward_schema_path=self.reward_schema_path,
            metadata=updated,
            output_dir=self.output_dir,
        )

