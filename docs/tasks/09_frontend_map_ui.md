# Task 09 — Frontend: Pixel Map UI

Parent: [../PRD.md](../PRD.md) · Depends on: [01_project_setup](./01_project_setup.md)

## Goal

The merchant's zero-cognitive-load view: a glanceable pixel-art map instead of a SaaS dashboard.

## Scope

- `frontend/src/components/Map.tsx` — a 2D isometric-styled canvas/DOM layout: pixelated "Hospital" on the left, "Godown" on the right, connected by a road (static art/CSS is fine for MVP; can be simple sprites/emoji-as-placeholder if final art assets aren't ready).
- `frontend/src/components/LeadIndicator.tsx` — animated exclamation mark over the Hospital when a new inbound WhatsApp message arrives (poll `GET /inventory`-adjacent status endpoint or a new lightweight `GET /api/v1/deals` list endpoint added alongside this task).
- `frontend/src/components/PaymentIndicator.tsx` — floating dollar-sign icon when a payment link is sent; turns green on confirmed payment.
- Framer Motion for all animations (per STORY.md §4).
- Simple polling (e.g., every 3-5s) against the backend for deal state changes; no WebSocket requirement for MVP.

## Out of Scope

- The dialogue box / audit trail detail view (Task 10).
- Final production art assets — placeholders are acceptable, structured so real sprites can drop in later.

## Acceptance Criteria

- [ ] Loading the frontend shows the Hospital/Godown/road layout.
- [ ] Simulating an inbound deal (via a test script hitting the backend) makes the exclamation mark appear over the Hospital within one polling interval.
- [ ] Simulating a payment-link-sent state shows the dollar icon; simulating payment-confirmed turns it green.

## Tests

- Component tests (React Testing Library) for `LeadIndicator` and `PaymentIndicator` rendering correctly for each state prop.
- A basic integration/smoke test that `Map` renders without crashing given a mocked deals list.
