# Task 10 — Frontend: Dialogue Audit Trail & Dispatch Animation

Parent: [../PRD.md](../PRD.md) · Depends on: [09_frontend_map_ui](./09_frontend_map_ui.md), [07_observability_tracing](./07_observability_tracing.md)

## Goal

Let the merchant click into a deal and see, at a glance, what the agent has done and why — without reading raw logs or traces.

## Scope

- `frontend/src/components/DialogueBox.tsx` — clicking the Hospital opens a retro RPG-style dialogue box showing the current high-level `DealState` stage in plain language (e.g., "Checking inventory... Stock found. Negotiating..."), sourced from a new lightweight backend endpoint that summarizes `DealState` (not raw Phoenix traces — that's the engineering-level detail, this is the merchant-level summary).
- `frontend/src/components/ReceiptFlash.tsx` — a pixelated "Receipt" icon that briefly flashes over the Godown once the invoice (Task 06) is sent.
- `frontend/src/components/DispatchSprite.tsx` — a pixelated delivery-driver sprite that animates from the Godown to the Hospital along the road once `status == Dispatched`, confirming paid + invoiced + fulfilled.
- Wire these to the same polling mechanism established in Task 09.

## Out of Scope

- Exposing raw Phoenix/OpenTelemetry trace data in the UI (that audience is the builder, not the merchant — link out to the Phoenix UI instead if useful).

## Acceptance Criteria

- [ ] Clicking the Hospital opens the dialogue box with the correct stage text for the current `DealState`.
- [ ] The dialogue box updates as the deal progresses through stages (verified by advancing a test deal through the backend and re-polling).
- [ ] The receipt flash and dispatch sprite animation both fire, in order, once a deal reaches `Dispatched`.

## Tests

- Component tests for `DialogueBox` given each `DealState.status` value, asserting the correct human-readable text.
- Component/animation tests for `ReceiptFlash` and `DispatchSprite` triggering only at the correct state transition (not before).

## Demo-day implementation notes (2026-09-05)

Time-boxed for a live demo recording. First pass (below, superseded) cut scope down to just `DispatchSprite`/`ReceiptFlash`; a follow-up request asked to build toward the full reference mockup instead, so the second pass (further below) is what actually shipped.

### Pass 1 (superseded) — minimal scene

Narrowed to Hospital ↔ road ↔ Godown, `LeadIndicator`/`PaymentIndicator` from Task 09, plus `DispatchSprite`/`ReceiptFlash`. No scenery, no demo-controls panel, no dialogue box — cut for a first, fast, working version.

### Pass 2 (shipped) — full scene matching the reference mockup

**Visual scene**, all in `frontend/src/components/Map.tsx` plus new sub-components: retro pixel-font title card (top-left, "Press Start 2P"/"VT323" via Google Fonts — see `index.html`/`index.css`), Hospital and "SAUDA HQ" building boxes with thick black borders and drop shadows, a dashed-yellow-line road, scattered 🌳 emoji scenery, a bottom `DialogueBox` showing the most recently active deal's last inbound buyer message, and a footer strip. Emoji placeholders throughout (🏥 🏭 🛵 🧾 🚨), same convention as Task 09 — no hand-drawn sprites, no ambulance/forklift/crowd art (out of reach in the time budget; CSS+emoji approximates the reference's density).

**`DemoControls.tsx`** — the reference mockup's "DEMO CONTROLS" panel, made *functional* rather than decorative: four buttons, each a `POST` to a new backend router, `backend/app/api/demo.py` (`/api/v1/demo/{whatsapp-lead,guardrail-block,razorpay-payment,ai-buyer-purchase}`), so a recording never needs a terminal alongside the browser:
- **Trigger WhatsApp Lead** — runs a canned two-message inbound conversation through the *real* agent graph (real Groq, real inventory lookup). Uses "Nitrile Examination Gloves" specifically because it's unambiguous in the mock catalog; a vaguer item name let the LLM's extraction land on a different, near-empty-stock SKU and made the demo unreliable (jumped straight to out-of-stock instead of the happy path).
- **Trigger Guardrail Block** — deliberately does *not* gamble on the LLM actually phrasing something unsafe on a given take. Runs a hardcoded unsafe draft reply through the real `check_text_guardrails()` and stores the real rewritten-safe result, so PRD §6 (no SLA/warranty promises) demos deterministically every click.
- **Trigger Razorpay Webhook** — finalizes whichever deal is most recently `AWAITING_PAYMENT` (WhatsApp conversations checked before agent-commerce orders), via a `finalize_payment()` helper extracted out of the real `/webhooks/razorpay` handler so both paths share identical logic — this is not a re-implementation, it's the real payment-confirmation code path, just skipping HMAC signature verification (the caller here is the merchant's own trusted UI, not an external webhook).
- **AI-Buyer Purchase** — same code path as a real `POST /api/v1/orders` call (Task 08), called directly rather than over HTTP so it doesn't need its own `AGENT_API_KEY`.

All four are deliberately unauthenticated, in-memory-store-mutating, demo-only endpoints — same "fine for a demo, not for prod" caveat as every other in-memory store in this codebase. Not for a real deployment.

**Bug found and fixed along the way, unrelated to the scene but demo-blocking:** `finalize_payment()`'s `whatsapp.send_message(...)` call had no try/except — with the mock WhatsApp credentials this repo is using in place of real Meta onboarding (see chat log / commit history around 2026-09-05), every single "Trigger Razorpay Webhook" click 500'd even though the payment/invoice logic itself succeeded and the state was already mutated. Wrapped in try/except, matching the same resilience pattern already applied to `app/api/whatsapp.py`'s webhook handler. This affects the *real* `/webhooks/razorpay` route too, not just the demo trigger — was a real latent bug.

**"SSE-like" live feel — still polling, not a real SSE endpoint** (unchanged reasoning from pass 1): `useDeals()` polls `GET /api/v1/deals` (now every 2s, tightened from 4s for a snappier demo feel), and `useDeliveryEvents(deals)` turns each state transition into a one-shot client-side animation (driver trip ~6s, receipt flash ~1.5s, guardrail siren ~1.5s) fired the instant it's first observed, Set-tracked per deal id so polling a deal sitting in a terminal/flagged state doesn't replay it. `GET /api/v1/deals` now also returns `messages`, `reply`, and `guardrail_violations` (added to `DealSummary` in `app/api/deals.py`) so the dialogue box and guardrail alert have something to show.

**`DialogueBox` is a simplified stand-in for this task's original click-to-open spec** — it's always visible (bottom bar, mockup-style) rather than click-triggered, and shows the raw last buyer message rather than a curated stage summary ("Checking inventory... Stock found..."). Revisit the original click-to-open + stage-summary version as a fast-follow if there's time after end-to-end testing; the acceptance criteria above describe that original version, not what shipped.
