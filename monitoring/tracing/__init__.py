"""Tracing utilities leveraging OpenTelemetry with graceful fallbacks."""

from .otel_config import get_tracer, init_tracing
from .instrumentors import span, span_async

__all__ = ["init_tracing", "get_tracer", "span", "span_async"]

