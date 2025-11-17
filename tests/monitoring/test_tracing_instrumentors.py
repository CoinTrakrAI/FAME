from monitoring.tracing import get_tracer, init_tracing, span


def test_span_context_noop_without_opentelemetry(monkeypatch):
    # Ensure init does not raise even if OTLP endpoint invalid when OTEL missing.
    init_tracing({"service_name": "TestService", "exporter_endpoint": None})

    with span("test_span"):
        tracer = get_tracer("test")
        # When OpenTelemetry is not installed, tracer will be None
        assert tracer is None or hasattr(tracer, "start_as_current_span")

