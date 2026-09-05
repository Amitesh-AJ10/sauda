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
