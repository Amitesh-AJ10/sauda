.PHONY: backend frontend test-backend

backend:
	cd backend && uv run uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && uv run pytest
