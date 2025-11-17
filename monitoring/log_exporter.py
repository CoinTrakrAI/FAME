"""
Log exporter for forwarding aggregated events to Elasticsearch or Splunk.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

try:  # optional dependency
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LogExporterConfig:
    batch_size: int = 200
    interval_seconds: float = 5.0
    elastic_url: Optional[str] = None
    elastic_index: str = "fame-logs"
    splunk_url: Optional[str] = None
    splunk_token: Optional[str] = None


class LogExporter:
    def __init__(self, aggregator, config: LogExporterConfig) -> None:
        self.aggregator = aggregator
        self.config = config
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_timestamp: Optional[datetime] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if not (self.config.elastic_url or self.config.splunk_url):
            logger.info("Log exporter configured without endpoints; skipping start.")
            return
        self._thread = threading.Thread(target=self._run, name="FAMELogExporter", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _run(self) -> None:
        logger.info("Log exporter thread started")
        while not self._stop_event.is_set():
            try:
                exported = self._export_batch()
                if exported:
                    logger.debug("Exported %s log events", exported)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Log export failed: %s", exc)
            finally:
                time.sleep(self.config.interval_seconds)

    def _export_batch(self) -> int:
        events = self._collect_events()
        if not events:
            return 0
        if self.config.elastic_url and requests:
            self._send_to_elastic(events)
        if self.config.splunk_url and self.config.splunk_token and requests:
            self._send_to_splunk(events)
        return len(events)

    def _collect_events(self) -> List[dict]:
        raw_events = self.aggregator.recent(self.config.batch_size)
        filtered: List[dict] = []
        for event in reversed(raw_events):  # chronological order
            timestamp = event.get("timestamp")
            if not timestamp:
                continue
            try:
                ts = datetime.fromisoformat(str(timestamp))
            except ValueError:
                continue
            if self._last_timestamp and ts <= self._last_timestamp:
                continue
            filtered.append(event)
        if filtered:
            latest_ts = datetime.fromisoformat(str(filtered[-1]["timestamp"]))
            self._last_timestamp = latest_ts
        return filtered

    def _send_to_elastic(self, events: List[dict]) -> None:
        if not requests:
            logger.warning("requests library unavailable; cannot export to Elasticsearch.")
            return
        bulk_endpoint = f"{self.config.elastic_url.rstrip('/')}/_bulk"
        lines = []
        for event in events:
            lines.append(json.dumps({"index": {"_index": self.config.elastic_index}}))
            lines.append(json.dumps(event))
        payload = "\n".join(lines) + "\n"
        response = requests.post(
            bulk_endpoint,
            data=payload,
            headers={"Content-Type": "application/x-ndjson"},
            timeout=10,
        )
        if response.status_code >= 400:
            logger.error("Elasticsearch bulk ingest failed: %s", response.text)

    def _send_to_splunk(self, events: List[dict]) -> None:
        if not requests:
            logger.warning("requests library unavailable; cannot export to Splunk.")
            return
        for event in events:
            payload = {"event": event}
            response = requests.post(
                self.config.splunk_url,
                data=json.dumps(payload),
                headers={
                    "Authorization": f"Splunk {self.config.splunk_token}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            )
            if response.status_code >= 400:
                logger.error("Splunk HEC ingest failed: %s", response.text)
                break

