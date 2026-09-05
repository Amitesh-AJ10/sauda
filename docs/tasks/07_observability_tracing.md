# Task 07 — Observability & Tracing

Parent: [../PRD.md](../PRD.md) · Depends on: [03_agent_orchestration](./03_agent_orchestration.md)

## Goal

An immutable, inspectable audit trail of every LangGraph node, LLM call, and guardrail decision — the thing that makes "explainable and bounded" more than a slogan.

## Scope

- Add Arize Phoenix + OpenTelemetry instrumentation to the backend:
  - `backend/app/observability/tracing.py` — sets up the OTel tracer provider, exports to Phoenix (`PHOENIX_COLLECTOR_ENDPOINT` env var; local Phoenix instance for dev).
  - Instrument each LangGraph node from Task 03 with a span (node name, inputs/outputs summarized, timestamps).
  - Instrument LLM calls (`services/llm.py`) with span attributes: prompt, response, model, latency.
  - Instrument guardrail checks explicitly as their own spans (e.g., `guardrail.price_bounds`, `guardrail.no_sla_promise`), recording pass/fail.
- Add a `GET /health/tracing` debug endpoint (or a README note) describing how to view traces in the local Phoenix UI.

## Out of Scope

- Any change to agent logic/behavior — this task only adds observation, not decisions.
- Production-grade trace storage/retention policy.

## Acceptance Criteria

- [ ] Running one deal end-to-end (using the Task 03 test scenarios) produces a visible trace in Phoenix with one span per node, correctly nested/ordered.
- [ ] Guardrail pass/fail is visible as span attributes or events, not just log lines.
- [ ] Turning tracing off (e.g., missing `PHOENIX_COLLECTOR_ENDPOINT`) doesn't break the agent — it should no-op gracefully.

## Tests

- Unit test that spans are created for each node during a graph run (assert on the in-memory span exporter used in tests, not a live Phoenix instance).
- Unit test that a guardrail rejection is recorded as a distinguishable span/event.
- Test the graceful no-op path when tracing config is absent.
