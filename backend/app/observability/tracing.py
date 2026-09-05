"""OpenTelemetry tracing, exported to a local Arize Phoenix instance.

Every LangGraph node, LLM call, and guardrail decision gets its own span so
a deal can be replayed and inspected after the fact — see
docs/tasks/07_observability_tracing.md.

Deliberately self-contained: instead of touching OpenTelemetry's global
`TracerProvider` registry (which refuses to be reconfigured once set, and
would make re-running `configure_tracing()` across tests noisy), this module
keeps its own module-level provider reference. `get_tracer()` hands out a
tracer from that provider when one has been configured, and falls back to
the OpenTelemetry API's default no-op tracer otherwise — so tracing is a
pure add-on: missing `PHOENIX_COLLECTOR_ENDPOINT` (or never calling
`configure_tracing()` at all) means every span call below is a harmless
no-op, not a crash.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter
from opentelemetry.trace import Span, Status, StatusCode

SERVICE_NAME = "sauda-backend"
TRACER_NAME = "sauda.agent"

_tracer_provider: TracerProvider | None = None


def configure_tracing(exporter: SpanExporter | None = None) -> TracerProvider | None:
    """Set up (or reset) tracing.

    - `exporter` given (e.g. an in-memory exporter in tests): always wire up
      a real `TracerProvider` using it, regardless of env vars.
    - `exporter` omitted: read `PHOENIX_COLLECTOR_ENDPOINT`. If unset, leave
      tracing off (`get_tracer()` will hand back a no-op tracer). If set,
      export to Phoenix over OTLP/HTTP.

    Returns the configured provider, or `None` if tracing stayed off.
    """
    global _tracer_provider

    endpoint = os.environ.get("PHOENIX_COLLECTOR_ENDPOINT")
    if exporter is None and not endpoint:
        _tracer_provider = None
        return None

    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
    if exporter is not None:
        provider.add_span_processor(SimpleSpanProcessor(exporter))
    else:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))

    _tracer_provider = provider
    return provider


def is_tracing_enabled() -> bool:
    return _tracer_provider is not None


def get_tracer(name: str = TRACER_NAME) -> trace.Tracer:
    """The active tracer, or a no-op one if tracing was never configured."""
    if _tracer_provider is None:
        return trace.get_tracer(name)  # OTel API default: a no-op tracer
    return _tracer_provider.get_tracer(name)


def _truncate(value: Any, limit: int = 2000) -> str:
    try:
        text = value if isinstance(value, str) else json.dumps(value, default=str)
    except TypeError:
        text = str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def traced_node(name: str) -> Callable[[Callable[..., dict]], Callable[..., dict]]:
    """Wrap a LangGraph node callable in a `node.<name>` span.

    Records a summary of the incoming state and the returned state updates;
    an exception raised by the node is recorded on the span and re-raised
    unchanged.
    """

    def decorator(fn: Callable[..., dict]) -> Callable[..., dict]:
        @wraps(fn)
        def wrapper(state, *args, **kwargs):
            tracer = get_tracer()
            with tracer.start_as_current_span(f"node.{name}") as span:
                span.set_attribute("node.name", name)
                dump = getattr(state, "model_dump", None)
                span.set_attribute("node.input", _truncate(dump() if dump else state))
                try:
                    result = fn(state, *args, **kwargs)
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(Status(StatusCode.ERROR, str(exc)))
                    raise
                span.set_attribute("node.output", _truncate(result))
                return result

        return wrapper

    return decorator


@contextmanager
def traced_guardrail(name: str) -> Iterator[Span]:
    """Run a guardrail check inside a `guardrail.<name>` span.

    The caller is responsible for setting `guardrail.passed` on the yielded
    span (and adding a `guardrail.violation` event on failure) — this just
    provides the span and the `guardrail.name` attribute.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(f"guardrail.{name}") as span:
        span.set_attribute("guardrail.name", name)
        yield span


def record_guardrail_result(span: Span, passed: bool, detail: str | None = None) -> None:
    """Tag a guardrail span with its pass/fail outcome."""
    span.set_attribute("guardrail.passed", passed)
    if not passed:
        span.add_event("guardrail.violation", {"detail": detail or ""})
