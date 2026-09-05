# Task 05 — Razorpay Payment Links

Parent: [../PRD.md](../PRD.md) · Depends on: [03_agent_orchestration](./03_agent_orchestration.md)

## Goal

Once terms are agreed in the negotiation, deterministically generate a real Razorpay Payment Link and detect when it's paid.

## Scope

- `backend/app/services/razorpay_client.py` — thin wrapper around the Razorpay Python SDK (or raw HTTPS calls), reading `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` from env.
  - `create_payment_link(amount_paise: int, description: str, notes: dict) -> PaymentLink` (calls `/v1/payment_links`).
- Wire the `await_payment` node (from Task 03) to actually call `create_payment_link` using the agreed `qty * unit_price`, and update `DealState` with the link URL + Razorpay `payment_link_id`.
- `backend/app/api/razorpay_webhooks.py`:
  - `POST /webhooks/razorpay` — verifies the webhook signature (`X-Razorpay-Signature` + webhook secret), and on `payment_link.paid`, looks up the `DealState` by `payment_link_id` and transitions `status` to `Paid`.
- Env vars: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`.

## Out of Scope

- Invoice generation (Task 06) — this task stops at "state = Paid".
- Retry/idempotency hardening beyond a basic duplicate-event guard (nice to have, not required for MVP).

## Acceptance Criteria

- [x] Negotiating a deal produces a real payment link (verified against Razorpay's test-mode API) with the correct amount.
- [x] A webhook signature that doesn't match the secret is rejected with `400`.
- [x] A valid `payment_link.paid` event transitions the matching deal to `Paid` and is a no-op if replayed (idempotent).

## Tests

- Unit test `create_payment_link` against a mocked HTTP layer (assert payload: amount, currency, description, notes).
- Unit test webhook signature verification (valid/invalid signature cases) using Razorpay's documented test payloads.
- Test the full negotiate → link created → webhook received → state transitions to `Paid` path with mocked Razorpay calls.
