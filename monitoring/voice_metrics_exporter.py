"""Voice telemetry exporter for observability integrations."""

from __future__ import annotations

import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional


logger = logging.getLogger(__name__)


class VoiceMetricsExporter:
    """Exports voice metrics in a Prometheus-friendly format."""

    def __init__(self, metrics_provider: Callable[[], str]) -> None:
        self._metrics_provider = metrics_provider
        self._http_server: Optional[HTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None

    def export_text(self) -> str:
        return self._metrics_provider()

    def start_http_server(self, host: str = "0.0.0.0", port: int = 8765) -> None:
        if self._http_server:
            logger.info("Voice metrics HTTP server already running")
            return

        exporter = self

        class MetricsHandler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                try:
                    payload = exporter.export_text().encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; version=0.0.4")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error("Voice metrics handler error: %s", exc)
                    self.send_response(500)
                    self.end_headers()

            def log_message(self, format, *args):  # noqa: A003
                logger.debug("VoiceMetricsExporter HTTP: " + format % args)

        self._http_server = HTTPServer((host, port), MetricsHandler)
        self._http_thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._http_thread.start()
        logger.info("Voice metrics HTTP server running on %s:%s", host, port)

    def stop_http_server(self) -> None:
        if self._http_server:
            self._http_server.shutdown()
            self._http_server.server_close()
            self._http_server = None
        if self._http_thread:
            self._http_thread.join(timeout=2)
            self._http_thread = None
        logger.info("Voice metrics HTTP server stopped")


__all__ = ["VoiceMetricsExporter"]


