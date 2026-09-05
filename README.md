# Sauda

**An autonomous B2B deal-maker for WhatsApp.** Built for the Razorpay Buildathon 2026 — Track 01: AI Growth and Agentic Commerce.

## The problem

Hospital procurement runs on WhatsApp, and B2B deals go to whoever replies first with an accurate quote. A merchant juggling godown logistics can't reply fast enough — every hour of delay is a lost order and a lost commission.

## The solution

Sauda intercepts inbound WhatsApp queries, checks live inventory, negotiates within pre-approved margins, generates a Razorpay Payment Link, and — once paid — auto-generates and sends a GST invoice, all without manual intervention. Pricing and stock decisions are deterministic Python, not LLM guesswork; every step is traced for audit.

Full background and rationale: [docs/STORY.md](docs/STORY.md). Requirements: [docs/PRD.md](docs/PRD.md).

## Architecture

- **Backend:** FastAPI + LangGraph (state machine: Extract Intent → Check Inventory → Negotiate → Await Payment → Issue Invoice → Dispatch) + Groq LLM + Pydantic guardrails + Arize Phoenix/OpenTelemetry tracing.
- **Data:** `mock_inventory.csv` — the godown's source of truth.
- **Payments:** Razorpay Payment Links, Webhooks, and Invoices APIs.
- **Frontend:** React (Vite) + Tailwind + Framer Motion — a retro pixel-art map (Hospital ↔ Godown) instead of a SaaS dashboard.

## Repo layout

```
backend/    FastAPI app, agent, integrations   (see docs/tasks/01_project_setup.md)
frontend/   Vite + React + Tailwind UI         (see docs/tasks/01_project_setup.md)
docs/
  STORY.md      the original problem/solution writeup
  PRD.md        product requirements derived from STORY.md
  tasks/        one sub-PRD per unit of work
```

## Getting started

Requires [`uv`](https://docs.astral.sh/uv/) for the backend and Node.js 20+ for the frontend.

```bash
# Backend
cd backend
cp .env.example .env   # fill in real keys
uv sync
uv run uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Or, from the repo root: `make backend`, `make frontend`, `make test-backend`.

## Known limitations

- Conversation state (per-sender `DealState`) lives in an in-memory dict, not a database — it resets on every backend restart. Acceptable for the buildathon demo; a real deployment needs durable storage.

## Status

In active development on `dev`, task by task per [docs/PRD.md §9](docs/PRD.md#9-milestones-maps-to-docstasks).

## License

TBD.
