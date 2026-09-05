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

Time-boxed for a live demo recording — cut for speed, not because the plan changed. Written against `Map.tsx` (Task 09), already merged.

**Visual scope, deliberately narrowed from the STORY.md §7 reference art:** just Hospital (left) ↔ road ↔ Godown/"Sauda HQ" (right), `LeadIndicator`/`PaymentIndicator` already there, plus the two pieces this note adds. No ambulance, forklift, crowd sprites, signage, or the dialogue/demo-controls chrome from the reference mock — those are art polish, not functional to the demo. Emoji placeholders throughout (🏥 🏭 🛵 🧾), same convention as Task 09.

**"SSE-like" live feel — polling, not a real SSE endpoint.** A real `text/event-stream` backend route would be the more "correct" push mechanism, but it's new backend surface with its own failure modes to debug under a 2-hour clock. Instead: keep Task 09's `useDeals()` poll (already built, already tested), and make each state transition fire a one-shot **client-side** animation of fixed duration (driver trip ~6s, receipt flash ~1.5s) the instant it's first observed — via a `useDeliveryEvents(deals)` hook that Set-tracks which deal ids have already fired which event, so a deal sitting in a terminal `dispatched` status across many polls doesn't replay its trip. The animation itself (via Framer Motion `transition.duration`) runs smoothly in the browser regardless of poll cadence — it doesn't visibly teleport between polls. Net effect reads as live/pushed without the new backend surface. Revisit true SSE post-demo if the polling gap (default 4s) ever reads as laggy.

**Trigger conditions** (derived from existing `DealState` fields, no new backend fields needed):
- `ReceiptFlash`: fires once per deal the first poll where `invoice_url` is non-null.
- `DispatchSprite`: fires once per deal the first poll where `status === "dispatched"`.
- Both can fire in the same poll tick for a fast-moving deal (e.g. a script that jumps straight to dispatched) — that's fine, no ordering dependency is enforced between them for this cut.

**Concurrency:** multiple simultaneously-dispatched deals render multiple driver sprites at once, vertically offset in the road lane so they don't overlap — no per-deal routing/positioning beyond that.

**`DialogueBox` (click-to-open audit trail) was cut from this pass** — the highest demo value was the moving-driver effect the recording needed; the dialogue box adds a new backend summary endpoint plus a click-driven modal, and didn't fit the remaining time. Comes back as a fast-follow if there's time after end-to-end testing.
