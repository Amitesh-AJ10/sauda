# Task 01 — Project Setup

Parent: [../PRD.md](../PRD.md)

## Goal

Stand up a minimal, structured repo skeleton so every later task has a place to land, with no speculative code.

## Scope

- `backend/` — Python (FastAPI) project.
  - `app/main.py` with a single `GET /health` endpoint.
  - `pyproject.toml` (managed via `uv`) pinning: `fastapi`, `uvicorn`, `pydantic`.
  - `.env.example` listing expected env vars (empty placeholders): `GROQ_API_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `PHOENIX_COLLECTOR_ENDPOINT`.
  - `.gitignore` for Python (`.venv/`, `__pycache__/`, `.env`).
- `frontend/` — Vite + React + TypeScript + Tailwind scaffold (via `npm create vite@latest`).
  - Default starter page is fine; no game assets yet.
  - `.gitignore` for Node (`node_modules/`, `dist/`).
- Root `.gitignore` merging both, if simpler than per-folder ones.
- A `Makefile` or simple npm/uv scripts to run backend and frontend locally (optional, keep it thin).

## Out of Scope

- Any business logic (inventory, agent, payments, WhatsApp).
- CI/CD pipelines.
- Docker.

## Acceptance Criteria

- [ ] `cd backend && uv run uvicorn app.main:app --reload` serves `GET /health` → `{"status": "ok"}`.
- [ ] `cd frontend && npm run dev` serves the default Vite app with Tailwind classes rendering (verify one styled element).
- [ ] Root README's "Getting Started" instructions work as written on a clean clone.

## Tests

- Backend: one `pytest` test hitting `/health` via `TestClient`, asserting `200` and the expected body.
- Frontend: no test required yet (no logic to test); a smoke test can be added once components exist.
