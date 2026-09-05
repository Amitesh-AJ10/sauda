# CLAUDE.md

Guidance for Claude Code (or any agent) working in this repo.

## What this is

Sauda — an autonomous WhatsApp B2B sales agent for a medical supplies distributor (Razorpay Buildathon 2026, Track 01). Full context: [docs/STORY.md](docs/STORY.md). Requirements: [docs/PRD.md](docs/PRD.md). Work breakdown: [docs/tasks/](docs/tasks/).

## How work is organized

Each file in `docs/tasks/` is a self-contained sub-PRD: goal, scope, explicit out-of-scope, acceptance criteria, and required tests. Work happens one task at a time, in order (they have dependencies on each other, noted at the top of each file).

The workflow per task:
1. Read the relevant `docs/tasks/NN_*.md` file in full before writing code.
2. Set up whatever environment/dependencies that task needs (installs, env vars from `.env.example`, etc.) before writing code.
3. Implement only what's in that task's Scope — resist pulling in later tasks' work early.
4. Write and pass the tests listed in that task's Tests section.
5. Commit and push to `dev` once tests pass. One task = one focused commit (or a small tight series if the task naturally splits).

**Superseded:** tasks 09/10's pixel-art frontend was fully replaced (clean dashboard + login-gated hospital chat + WhatsApp-style UI, real negotiation loop) on `redesign/clean-ui`, iterating directly from live testing rather than the docs/tasks/tests-first flow above. Treat `docs/tasks/09_*`/`10_*` as historical context for *what* shipped originally, not as the current source of truth for the frontend or the agent's conversation flow — read the code in `frontend/src/` and `backend/app/agent/` instead.

## Ground rules

- **Keep it simple.** This is a buildathon-scoped MVP, not a platform. Prefer the boring, direct implementation over an abstraction that anticipates future needs. In-memory state and mocked data are acceptable where a task says so — don't upgrade them unasked.
- **Guardrails are not optional.** Per `docs/PRD.md` §6: the LLM never states SLAs or warranties, never invents stock, and never computes the final price — Python does. Any code touching pricing or stock must be deterministic and testable without an LLM in the loop.
- **Don't scope-creep across task boundaries.** If task 03 needs something from task 05, that's a sign the task order or split needs revisiting — raise it, don't silently pull the later task forward.
- **Tests are part of the task, not an afterthought.** A task isn't done until its listed tests exist and pass.
- **No secrets in the repo.** Real API keys (Groq, Razorpay, WhatsApp) live in `.env`, never `.env.example` or committed files.
- **Commit hygiene:** commit messages should name the task (e.g., `feat: inventory service (task 02)`), stay focused on that task's diff, and land on `dev` (not `main`).

## Repo layout

```
backend/    FastAPI app, LangGraph agent, Razorpay/WhatsApp integrations
frontend/   Vite + React + Tailwind clean dashboard + WhatsApp-style hospital chat
docs/       STORY.md, PRD.md, DESIGN.md, tasks/
```
