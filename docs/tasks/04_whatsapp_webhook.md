# Task 04 — WhatsApp Webhook

Parent: [../PRD.md](../PRD.md) · Depends on: [03_agent_orchestration](./03_agent_orchestration.md)

## Goal

Connect the agent graph to real inbound/outbound WhatsApp messages via the WhatsApp Cloud API.

## Scope

- `backend/app/api/whatsapp.py`:
  - `GET /webhooks/whatsapp` — verification handshake (`hub.challenge` echo per Meta's spec).
  - `POST /webhooks/whatsapp` — receives inbound message payloads, extracts sender + text, loads/creates the corresponding `DealState` (in-memory dict keyed by sender phone number is fine for MVP), runs it through the LangGraph graph, and sends the resulting message back.
- `backend/app/services/whatsapp.py` — `send_message(to: str, text: str)` wrapper around the Cloud API's `/messages` endpoint.
- Env vars: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`.

## Out of Scope

- Persisting conversation state to a real database (in-memory is fine for the buildathon scope; note this as a known limitation in the README).
- Media messages (images/PDFs) inbound — outbound PDF invoice links are handled in Task 06.

## Acceptance Criteria

- [ ] Webhook verification handshake passes Meta's test (`GET` echoes challenge when `verify_token` matches).
- [ ] A simulated inbound text message payload (posted via test client, not real WhatsApp) drives the agent graph and triggers exactly one outbound `send_message` call with a well-formed reply.
- [ ] Unknown senders start a fresh `DealState`; known senders resume theirs.

## Tests

- Unit test the webhook verification path (correct token → 200 + challenge; wrong token → 403).
- Unit test `POST /webhooks/whatsapp` with a mocked `WhatsAppService.send_message` and a mocked agent graph run, asserting the right calls happen.
- Test state resumption across two sequential messages from the same sender.
