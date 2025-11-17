"""Policy promotion and rollback tooling."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Dict, List, Optional

import yaml


DEFAULT_POLICY_DIR = Path("models/policies")
DEFAULT_ACTIVE_FILE = DEFAULT_POLICY_DIR / "active_policy.yaml"


@dataclass(slots=True)
class PromotionManager:
    """Manage active policy metadata."""

    policy_dir: Path = field(default=DEFAULT_POLICY_DIR)
    active_file: Path = field(default=DEFAULT_ACTIVE_FILE)

    def __post_init__(self) -> None:
        self.policy_dir.mkdir(parents=True, exist_ok=True)

    # State handling -----------------------------------------------------

    def load_state(self) -> Dict:
        if not self.active_file.exists():
            return {"history": []}
        with self.active_file.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {"history": []}

    def write_state(self, state: Dict) -> None:
        with self.active_file.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(state, handle, sort_keys=False)

    # Metadata helpers ---------------------------------------------------

    def list_policies(self) -> List[str]:
        return sorted(entry.name for entry in self.policy_dir.iterdir() if entry.is_dir())

    def show_active(self) -> Dict:
        return self.load_state().get("current") or {}

    def promote(self, run_id: str, note: Optional[str] = None) -> Dict:
        run_path = self.policy_dir / run_id
        if not run_path.exists():
            raise FileNotFoundError(f"Policy directory not found: {run_path}")
        report = run_path / "training_report.json"
        metadata = {}
        if report.exists():
            try:
                metadata = json.loads(report.read_text(encoding="utf-8"))
            except Exception:
                metadata = {}

        state = self.load_state()
        history = state.get("history") or []
        current = state.get("current")
        if current:
            history.insert(0, current)
            history = history[:20]

        new_state = {
            "current": {
                "run_id": run_id,
                "promoted_at": datetime.now(timezone.utc).isoformat(),
                "note": note,
                "metadata": metadata,
            },
            "history": history,
        }
        self.write_state(new_state)
        return new_state["current"]

    def rollback(self) -> Dict:
        state = self.load_state()
        history = state.get("history") or []
        if not history:
            raise RuntimeError("No historical policy to roll back to.")
        new_current = history.pop(0)
        new_state = {"current": new_current, "history": history}
        self.write_state(new_state)
        return new_current


# Convenience functions ------------------------------------------------------

def promote_policy(run_id: str, note: Optional[str] = None) -> Dict:
    return PromotionManager().promote(run_id, note=note)


def rollback_policy() -> Dict:
    return PromotionManager().rollback()


def list_policies() -> List[str]:
    return PromotionManager().list_policies()


def show_active_policy() -> Dict:
    return PromotionManager().show_active()


# CLI ------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Policy promotion tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    promote_cmd = sub.add_parser("promote", help="Promote a policy run id")
    promote_cmd.add_argument("run_id")
    promote_cmd.add_argument("--note", help="Optional promotion note")

    sub.add_parser("rollback", help="Rollback to previously active policy")
    sub.add_parser("list", help="List available policy run ids")
    sub.add_parser("active", help="Show current active policy metadata")

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    manager = PromotionManager()

    if args.command == "promote":
        current = manager.promote(args.run_id, note=args.note)
        print(yaml.safe_dump(current, sort_keys=False))
    elif args.command == "rollback":
        current = manager.rollback()
        print(yaml.safe_dump(current, sort_keys=False))
    elif args.command == "list":
        for run_id in manager.list_policies():
            print(run_id)
    elif args.command == "active":
        print(yaml.safe_dump(manager.show_active(), sort_keys=False))
    else:  # pragma: no cover
        parser.print_help()


if __name__ == "__main__":
    main()

