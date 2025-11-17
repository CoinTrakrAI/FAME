from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:  # optional dependency
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
except ImportError:  # pragma: no cover - fallback if OTEL not installed
    trace = None  # type: ignore

_INITIALISED = False


def init_tracing(config: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialise global tracer provider if OpenTelemetry is available.

    Args:
        config: Optional dictionary with keys
            - service_name
            - exporter_endpoint
            - headers
    """
    global _INITIALISED
    if _INITIALISED:
        return
    if trace is None:
        logger.info("OpenTelemetry not installed; tracing disabled.")
        return

    config = config or {}
    service_name = config.get("service_name", "FAME")
    endpoint = config.get("exporter_endpoint")
    headers = config.get("headers") or {}

    resource = Resource(attributes={"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if endpoint:
        try:
            exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)
            logger.info("OpenTelemetry OTLP exporter initialised", extra={"endpoint": endpoint})
        except Exception as exc:  # pragma: no cover - defensive path
            logger.error("Failed to initialise OTLP exporter: %s", exc)

    trace.set_tracer_provider(provider)
    _INITIALISED = True


def get_tracer(name: str = "FAME") -> Any:
    if trace is None:
        return None
    return trace.get_tracer(name)

