#!/usr/bin/env python3
"""
Docker healthcheck script for FAME containers.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    endpoint = os.environ.get("FAME_HEALTH_URL", "http://127.0.0.1:8080/readyz")
    try:
        with urllib.request.urlopen(endpoint, timeout=5) as response:
            if response.status != 200:
                return 1
            payload = json.loads(response.read().decode("utf-8"))
            status = payload.get("status") or payload.get("overall_status")
            if status not in ("ready", "healthy"):
                return 1
    except (urllib.error.URLError, json.JSONDecodeError):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

