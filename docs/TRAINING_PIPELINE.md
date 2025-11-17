## Stage 5 Training Pipeline

### Overview
FAME now supports both offline and online policy updates driven by telemetry. The workflow is split into three layers:

1. **Telemetry capture** – conversation responses, trading outcomes, and explicit feedback are written to `telemetry/feedback/events_YYYYMMDD.jsonl`.
2. **Feature preparation** – `FeedbackCollector` + `FeatureSetBuilder` consolidate raw events into curated datasets under `data/training/` and `data/feature_store/`.
3. **Policy training** – offline batches (`run_policy_update.py`) and incremental online updates (`run_online_update.py`) feed the shared `ReinforcementTrainer`.

```
Runtime (brain/trading) ──> telemetry/events.py ──> JSONL sink
                                      │
                                      ├─ Offline: FeedbackCollector → FeatureSetBuilder → OfflinePolicyTrainer
                                      └─ Online: OnlinePolicyTrainer buffer → RewardEngine → ReinforcementTrainer
```

### Key Components

| Path | Description |
|------|-------------|
| `telemetry/events.py` | Emits JSONL records (one event per line) containing session id, intent, skill, score, trade ROI, preferences hash, latency, confidence. |
| `training/context.py` | Run metadata (run_id, timestamps, config paths) shared by all pipelines. |
| `training/configs/training_config.yaml` | Batch sizes, learning rate, drift thresholds, online buffer sizes. |
| `training/configs/reward_schema.yaml` | Reward weights for explicit feedback, ROI scaling, latency bonuses, guardrail penalties. |
| `training/rewards.py` | Converts telemetry events into bounded scalar rewards. |
| `training/pipelines/collect_feedback.py` | Deduplicates JSONL sources and produces `feedback_<run_id>.jsonl`. |
| `training/pipelines/build_feature_set.py` | Normalises events into a consistent feature schema and persists via `analytics/feature_store.FeatureStore`. |
| `training/pipelines/run_policy_update.py` | Loads offline dataset, summarises metrics, and (when torch is available) kicks off batch reinforcement training. |
| `training/pipelines/run_online_update.py` | Maintains an event buffer, computes rewards, checks drift, calls `ReinforcementTrainer.train_from_events`, and logs metrics/checkpoints. |
| `analytics/feature_store.py` | Simple JSONL-based storage for feature datasets (offline and online batches). |
| `intelligence/reinforcement_trainer.py` | Encodes events to state vectors, manages PPO-style updates, and tracks average rewards. |

### Offline Training Flow
1. Schedule `collect_feedback.py` (e.g., cron/nightly) to gather new telemetry.
2. Run `build_feature_set.py` to produce `data/feature_store/features_<run_id>.jsonl`.
3. Execute `run_policy_update.py` to feed the dataset into `ReinforcementTrainer`. A `training_report.json` is written to `models/policies/<run_id>/`.
4. Review evaluation metrics, then promote the new policy by updating `active_policy.yaml` (promotion tooling in progress).

### Online Training Flow
1. Runtime emits telemetry in real-time (already wired in `orchestrator/brain`, `TradingService`).
2. `OnlinePolicyTrainer` buffers incoming events (from a queue or direct calls), computes rewards using `RewardEngine`, and checks reward drift against `drift_kl_threshold`.
3. If safe, it calls `ReinforcementTrainer.train_from_events(...)`, saves the batch via `FeatureStore`, and logs metrics. If drift exceeds the guardrail it aborts the update and clears the buffer.
4. Policy snapshots can be exported from `models/policies/<run_id>_online` for review or promotion.

### Safety & Guardrails
- **Telemetry validation**: `emit_training_event` ensures `session_id` and `timestamp` are set, warns on missing data.
- **Reward bounding**: `RewardEngine` clips ROI contributions and overall reward to [-5, +5].
- **Drift detection**: Online trainer compares average reward to the recent baseline, skipping updates when exceeding the threshold.
- **Persistence**: Each batch (offline and online) is stored via `FeatureStore` for auditability and replay.
- **Rollback hooks**: Policies are stored per run id; runtime promotion remains explicit so we can revert quickly.

### Next Steps
- Add queue (Kafka/Redis) integration for streaming ingestion.
- Extend promotion CLI to load/export policy weights and update `active_policy.yaml`.
- Build Grafana dashboards for training metrics (`avg_reward`, `updates_total`, drift alarms).
- Automate documentation of each run (`reports/training_run_<id>.md`) with key metrics and guardrail status.

- Prometheus/Grafana monitoring templates now live under `monitoring/` (`prometheus_metrics.py`, `prometheus/alert_rules.yaml`, `grafana/dashboards/trading_ai_overview.yaml`). Use `setup_comprehensive_monitoring(...)` to instrument training, strategy, and risk systems.

### Promotion & Rollback
- Use `python -m training.promotion promote <run_id> [--note "..."]` to mark a policy as active. The tool records metadata (including the run’s `training_report.json`) in `active_policy.yaml` and tracks history.
- `python -m training.promotion rollback` reverts to the previous active entry.
- `python -m training.promotion list` enumerates available run directories under `models/policies/`.

