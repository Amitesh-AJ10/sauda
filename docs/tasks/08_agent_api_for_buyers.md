# Task 08 — Machine-Readable API for AI Buyer Agents

Parent: [../PRD.md](../PRD.md) · Depends on: [02_inventory_service](./02_inventory_service.md), [05_razorpay_payment_links](./05_razorpay_payment_links.md)

## Goal

Make the merchant "sellable to AI buyers" (Track 01 mandate): a hospital's own procurement AI agent should be able to fetch a quote and pay without a WhatsApp conversation.

## Scope

- `backend/app/api/agent_commerce.py`:
  - `POST /api/v1/quote` — structured JSON request `{item_name, qty, pin_code}` → structured JSON response `{available_qty, unit_price, total_price, currency}` (reuses `InventoryService` and the same deterministic pricing logic as `negotiate`, no LLM round-trip needed for a fully-specified request).
  - `POST /api/v1/orders` — structured JSON request confirming a quote → creates a Razorpay Payment Link (reuses Task 05's `create_payment_link`) and returns `{order_id, payment_link_url, status}`.
  - `GET /api/v1/orders/{order_id}` — returns current `DealState.status` for polling.
- Document the API with FastAPI's auto-generated OpenAPI schema (already free from FastAPI — just make sure request/response models are clean Pydantic models so the schema is accurate).
- Basic auth: a static API key header (`X-API-Key`) checked against an env var, enough to prevent open abuse without building a full auth system.

## Out of Scope

- OAuth/full auth system (explicitly a non-goal in the PRD).
- Rate limiting (nice to have, not required for MVP).

## Acceptance Criteria

- [ ] `POST /api/v1/quote` with a valid, in-stock item returns a correct price with no LLM call involved.
- [ ] `POST /api/v1/quote` for an over-stock request returns the available quantity instead of erroring silently.
- [ ] `POST /api/v1/orders` produces the same kind of real Razorpay payment link as the WhatsApp flow, and `GET /api/v1/orders/{order_id}` reflects state changes after payment.
- [ ] Requests missing/with a wrong `X-API-Key` are rejected with `401`.

## Tests

- API tests for `/quote` (happy path, over-stock, unknown item).
- API test for `/orders` creation (mocked Razorpay call) and `/orders/{id}` status polling before and after a simulated payment webhook.
- Auth test for missing/invalid API key on all three endpoints.
