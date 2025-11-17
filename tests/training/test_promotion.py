from datetime import datetime
import json
from pathlib import Path

from training.promotion import PromotionManager


def test_policy_promote_and_rollback(tmp_path: Path):
    policy_dir = tmp_path / "policies"
    manager = PromotionManager(policy_dir=policy_dir, active_file=policy_dir / "active.yaml")

    run1 = policy_dir / "run1"
    run1.mkdir(parents=True)
    (run1 / "training_report.json").write_text(json.dumps({"metrics": {"score": 0.7}}), encoding="utf-8")

    run2 = policy_dir / "run2"
    run2.mkdir(parents=True)
    (run2 / "training_report.json").write_text(json.dumps({"metrics": {"score": 0.8}}), encoding="utf-8")

    active = manager.promote("run1", note="baseline")
    assert active["run_id"] == "run1"
    assert manager.show_active()["run_id"] == "run1"

    active = manager.promote("run2")
    assert active["run_id"] == "run2"
    assert manager.show_active()["run_id"] == "run2"
    assert manager.list_policies() == ["run1", "run2"]

    rolled = manager.rollback()
    assert rolled["run_id"] == "run1"
    assert manager.show_active()["run_id"] == "run1"

