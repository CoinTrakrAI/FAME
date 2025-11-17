"""
Simple in-memory log aggregator used by the production logger.
"""

from __future__ import annotations

import json
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, List, Optional


class LogAggregator:
    def __init__(self, max_events: int = 1000) -> None:
        self._buffer: Deque[Dict[str, object]] = deque(maxlen=max_events)
        self._lock = threading.Lock()

    def emit(self, level: str, message: str, **fields: object) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "message": message,
            "fields": fields,
        }
        with self._lock:
            self._buffer.appendleft(payload)

    def emit_json(self, payload: Dict[str, object]) -> None:
        with self._lock:
            payload = dict(payload)
            payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
            self._buffer.appendleft(payload)

    def recent(self, limit: int = 100) -> List[Dict[str, object]]:
        with self._lock:
            return list(self._buffer)[:limit]

    def to_json(self, limit: int = 100) -> str:
        return json.dumps({"events": self.recent(limit), "count": len(self._buffer)}, indent=2)

