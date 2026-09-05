# Task 03 — Agent Orchestration (LangGraph)

Parent: [../PRD.md](../PRD.md) · Depends on: [02_inventory_service](./02_inventory_service.md)

## Goal

The core state machine: Extract Intent → Check Inventory → Negotiate → Await Payment → Issue Invoice → Dispatch, with the LLM strictly confined to language, and Python owning every decision that touches money or stock.

## Scope

- `backend/app/agent/state.py` — a `DealState` Pydantic/TypedDict model: buyer message history, extracted `item_name`, `qty`, `hospital_name`, `pin_code`, `unit_price`, `status` (enum matching the six stages).
- `backend/app/agent/prompts.py` — the system prompt from STORY.md §5, stored as a constant (not re-derived per call).
- `backend/app/agent/nodes.py` — one function per LangGraph node:
  - `extract_intent` (LLM call → structured output validated against a Pydantic schema).
  - `check_inventory` (calls `InventoryService`, deterministic).
  - `negotiate` (Python computes the approved price band; LLM only phrases the message — see guardrail F/G3 in the PRD).
  - `await_payment`, `issue_invoice`, `dispatch` — stubs that just transition state for now (real integration lands in Tasks 05/06).
- `backend/app/agent/graph.py` — wires the nodes into a LangGraph `StateGraph` with the linear flow above (branches for "out of stock" / "declined" are fine to add if trivial).
- `backend/app/services/llm.py` — thin Groq client wrapper (`qwen/qwen3.8-27b`), reads `GROQ_API_KEY` from env.
- Guardrail checks live in Python, not prompt text: reject/clamp any LLM-proposed price outside the approved band; reject any LLM output that mentions delivery time or warranty (simple keyword/regex check is enough for MVP).

## Out of Scope

- Wiring to real WhatsApp or Razorpay (later tasks call into this graph).
- Tracing (Task 07) — leave clean seams (e.g., call nodes as plain functions) so tracing can wrap them later without a rewrite.

## Acceptance Criteria

- [x] Given a canned buyer message ("Need 500 surgical staplers to Pune, best rate?"), the graph runs end-to-end (with `await_payment`/`issue_invoice`/`dispatch` as stubs) and produces a final `DealState` with `status` progressed correctly.
- [x] An out-of-stock request short-circuits with an apology + available quantity, never inventing stock.
- [x] A guardrail test proves an LLM output containing "delivered in 10 minutes" or "we guarantee" is caught and rewritten/rejected before reaching the buyer.

## Tests

- Unit test each node function with a mocked LLM client (no real API calls in CI).
- Integration test running the full graph on 2-3 canned scenarios: in-stock happy path, out-of-stock, guardrail violation caught.
