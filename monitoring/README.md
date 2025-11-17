# FAME Observability Guide

Enterprise monitoring for voice and trading subsystems using Prometheus and Grafana.

## 1. Exporter Endpoints

### Voice Telemetry

```bash
set FAME_VOICE_METRICS_PORT=8765
python fame_voice_main.py
# Metrics: http://localhost:8765/metrics
# Health : http://localhost:8765/health
```

### Trading Telemetry

```bash
set FAME_TRADING_METRICS_PORT=8775
python fame_unified.py
# Metrics: http://localhost:8775/metrics
# Health : http://localhost:8775/health
```

## 2. Prometheus Configuration

`prometheus.yml` snippet:

```yaml
scrape_configs:
  - job_name: fame_voice
    metrics_path: /metrics
    static_configs:
      - targets: ['voice-host:8765']
  - job_name: fame_trading
    metrics_path: /metrics
    static_configs:
      - targets: ['trading-host:8775']
```

## 3. Importing Grafana Dashboards

1. Open Grafana → Dashboards → Import.
2. Upload dashboard bundles:
   - `monitoring/dashboard_templates/voice_dashboard.json`
   - `monitoring/dashboard_templates/trading_dashboard.json`
   - `monitoring/grafana/dashboards/business_kpi.yaml`
   - `monitoring/grafana/dashboards/training_overview.yaml`
3. Choose Prometheus datasource when prompted.

## 4. Alert Rules

Alert rule templates are provided in `monitoring/alert_rules/` and can be loaded directly by Prometheus.

- `trading_alerts.yaml` – API health, ROI/win-rate, signal stalls, plus execution latency/slippage/rejection monitors.
- `voice_alerts.yaml` – exporter availability, latency thresholds, wake-word anomalies.
- `business_alerts.yaml` – projected ROI drawdowns, win-rate collapses, voice conversion drops, and conversation training stalls.
- `training_alerts.yaml` – reward regression, win-rate collapse, drift spikes, latency breaches, and experience buffer stalls.

Add to `prometheus.yml`:

```yaml
rule_files:
  - monitoring/alert_rules/trading_alerts.yaml
  - monitoring/alert_rules/voice_alerts.yaml
  - monitoring/alert_rules/business_alerts.yaml
  - monitoring/alert_rules/training_alerts.yaml
```

## 5. Business KPI Tracking

Trading metrics now publish:

- `trading_projected_roi_avg`
- `trading_executed_trades`
- `trading_win_trades`, `trading_loss_trades`
- Voice metrics include success rates (`trading_voice_total_requests` / `trading_voice_failed_requests`) and wake-word events.
- Conversation training velocity derived from `training_cycles_total{training_type="conversation"}`.
- Training performance snapshots publish `training_policy_reward_avg`, `training_policy_win_rate`, `training_policy_rolling_roi`, `training_policy_latency_ms`, `training_policy_drift_score_*`, and `training_experience_buffer_size`.

## 6. Continuous Exporter Tasks

Run exporters under systemd or Docker to keep metrics active. Example:

```bash
python -c "import asyncio; from monitoring.trading_metrics_exporter import create_trading_exporter; from services.trading_service import TradingConfig, get_trading_service; async def main(): service = await get_trading_service(TradingConfig()); exporter = create_trading_exporter(service.telemetry); await exporter.continuous_export(30); asyncio.run(main())"
```

## 7. Next Steps

- Connect Grafana alerts to Slack/Teams.
- Export store dashboards in Git for change control.
- Enable JSON log aggregation by setting:
  - `FAME_LOG_AGGREGATION=1`
  - `FAME_LOG_BUFFER=500` (optional buffer tuning)
  - `FAME_LOG_ELASTIC_URL=https://elastic.example.com/logs` (optional)
  - `FAME_LOG_ELASTIC_INDEX=fame-logs` (optional)
  - `FAME_LOG_SPLUNK_HEC=https://splunk.example.com/services/collector` with `FAME_LOG_SPLUNK_TOKEN=<token>` (optional)
  - `FAME_LOG_EXPORT_INTERVAL=5` (seconds between batches)
- Aggregate logs with Elastic/Loki and trace pipelines via OpenTelemetry.

Observability stack is ready for production deployment. Customize dashboards as needed. Additional modules can replicate this pattern.

