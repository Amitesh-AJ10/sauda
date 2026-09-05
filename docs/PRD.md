# Sauda — Product Requirements Document

Source of truth for scope: [STORY.md](./STORY.md) (Razorpay Buildathon 2026, Track 01: AI Growth and Agentic Commerce).
This PRD translates the story into buildable requirements. Implementation work is split into the sub-PRDs under [tasks/](./tasks/).

## 1. Problem

B2B medical supply deals over WhatsApp are won on "speed to lead." The merchant (a solo distributor) cannot check stock, price a quote, and reply fast enough while managing physical logistics. Slow replies lose the order — and the Razorpay transaction — to a faster-replying competitor.

## 2. Goal

Let an autonomous agent go from **one inbound WhatsApp message → a closed, paid, invoiced deal** in minutes, with no manual intervention from the merchant, while keeping every pricing/financial decision deterministic and auditable.

## 3. Users

- **Primary: The Merchant** (e.g., a distributor owner). Wants zero missed leads and zero cognitive load — a glanceable view of what the agent is doing, not a dashboard to operate.
- **Secondary: The Buyer** (hospital procurement staff, human or an AI purchasing agent). Wants a fast, accurate quote and a frictionless way to pay and receive a GST invoice.

## 4. Non-Goals (for this build)

- Real freight/logistics cost calculation (stubbed/simulated; see STORY.md §8 Future Scope).
- Multi-merchant / multi-tenant support.
- A production-grade auth/user-management system beyond what's needed to secure the merchant's own endpoints.
- Real WhatsApp Business account approval flow (use the Cloud API sandbox/test number).

## 5. Functional Requirements

| # | Requirement | Notes |
|---|---|---|
| F1 | Ingest inbound WhatsApp messages via webhook | See [04_whatsapp_webhook](./tasks/04_whatsapp_webhook.md) |
| F2 | Extract buyer intent (item, qty, delivery PIN) from free-text | LLM node, guarded by Pydantic schema |
| F3 | Check live stock against `mock_inventory.csv` | Never let the LLM invent stock — deterministic lookup |
| F4 | Negotiate price within merchant-approved margin bounds | Math done in Python, never by the LLM |
| F5 | Generate a Razorpay Payment Link once terms are agreed | See [05_razorpay_payment_links](./tasks/05_razorpay_payment_links.md) |
| F6 | Listen for `payment.link.paid` webhook and update deal state | |
| F7 | Auto-generate a GST invoice via Razorpay Invoices API on payment | See [06_razorpay_invoicing](./tasks/06_razorpay_invoicing.md) |
| F8 | Push the invoice PDF link back to the buyer over WhatsApp | Closes the loop with zero manual paperwork |
| F9 | Expose a machine-readable quote/order API for AI buyer agents | See [08_agent_api_for_buyers](./tasks/08_agent_api_for_buyers.md) |
| F10 | Trace every LangGraph node, LLM call, and guardrail check | Arize Phoenix + OpenTelemetry |
| F11 | Visualize the deal lifecycle on a pixel-art map UI | Hospital ↔ Godown, per STORY.md §7 |

## 6. Guardrails (must hold for every deal)

1. The LLM never states delivery SLAs or warranties.
2. The LLM never fabricates stock — quantities always come from `mock_inventory.csv`.
3. Final price is computed by deterministic Python from approved parameters, never by the LLM.
4. Every state transition (Extract Intent → Check Inventory → Negotiate → Await Payment → Issue Invoice → Dispatch) is traced and inspectable.
5. Payment links and invoices are only created by backend code reacting to validated state — never directly from LLM output.

## 7. Architecture Summary

See STORY.md §4–§6 for full detail. Short version:

- **Backend:** FastAPI + LangGraph state machine, Groq LLM (`qwen/qwen3.8-27b`) for NLU/NLG, Pydantic guardrails, Arize Phoenix/OpenTelemetry tracing.
- **Data:** `mock_inventory.csv` (`product_id, item_name, stock_qty, base_price, notes`).
- **Payments:** Razorpay Payment Links, Webhooks, Invoices APIs.
- **Frontend:** React (Vite) + Tailwind + Framer Motion, retro 8-bit isometric map.

## 8. Success Metrics

- Time from inbound message to payment link sent (target: minutes, not hours).
- % of deals fully closed (quoted → paid → invoiced) without manual merchant input.
- Zero guardrail violations (no invented stock, no SLA/warranty promises, no off-margin pricing) across traced sessions.

## 9. Milestones (maps to `docs/tasks/`)

1. [01_project_setup](./tasks/01_project_setup.md) — repo scaffold, envs, tooling.
2. [02_inventory_service](./tasks/02_inventory_service.md) — inventory data + API.
3. [03_agent_orchestration](./tasks/03_agent_orchestration.md) — LangGraph agent + guardrails.
4. [04_whatsapp_webhook](./tasks/04_whatsapp_webhook.md) — inbound/outbound WhatsApp.
5. [05_razorpay_payment_links](./tasks/05_razorpay_payment_links.md) — payment link generation + webhook.
6. [06_razorpay_invoicing](./tasks/06_razorpay_invoicing.md) — GST invoice on payment.
7. [07_observability_tracing](./tasks/07_observability_tracing.md) — Phoenix/OpenTelemetry tracing.
8. [08_agent_api_for_buyers](./tasks/08_agent_api_for_buyers.md) — machine-readable API for AI buyers.
9. [09_frontend_map_ui](./tasks/09_frontend_map_ui.md) — pixel map, leads, payment/invoice visuals.
10. [10_frontend_dialogue_audit](./tasks/10_frontend_dialogue_audit.md) — RPG dialogue audit trail + dispatch animation.

Tasks are ordered so each one is independently testable and builds on the last. Each sub-PRD is scoped to be implemented, tested, and shipped as its own commit.
