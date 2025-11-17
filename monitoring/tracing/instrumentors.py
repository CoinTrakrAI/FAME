from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

from .otel_config import get_tracer


@contextmanager
def span(name: str, attributes: Optional[Dict[str, Any]] = None) -> Iterator[Any]:
    tracer = get_tracer()
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(name) as current_span:
        if attributes:
            for key, value in attributes.items():
                if value is not None:
                    current_span.set_attribute(key, value)
        yield current_span


@contextmanager
def span_async(name: str, attributes: Optional[Dict[str, Any]] = None) -> Iterator[Any]:
    # Async-friendly variant (same implementation thanks to OpenTelemetry context management).
    with span(name, attributes) as current_span:
        yield current_span

