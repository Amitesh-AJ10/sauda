import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Load backend/.env into the process before anything below reads os.environ.
# Real env vars (e.g. set in CI or a deploy) always win — load_dotenv never
# overrides a var that's already set.
load_dotenv()

from app.api.agent_commerce import router as agent_commerce_router
from app.api.deals import router as deals_router
from app.api.razorpay_webhooks import router as razorpay_router
from app.api.whatsapp import router as whatsapp_router
from app.models.inventory import InventoryItem
from app.observability import tracing
from app.services.inventory import get_inventory_service


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    # Wire up Phoenix tracing if `PHOENIX_COLLECTOR_ENDPOINT` is set. Left
    # unset, `tracing.get_tracer()` falls back to a no-op tracer everywhere
    # it's used — the agent runs exactly the same either way.
    tracing.configure_tracing()
    yield


app = FastAPI(title="Sauda", lifespan=_lifespan)
# Dev-only: lets the Vite dev server (a different origin) poll the API
# directly. Tighten to a specific origin before this goes past a demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(whatsapp_router)
app.include_router(razorpay_router)
app.include_router(agent_commerce_router)
app.include_router(deals_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/tracing")
def health_tracing() -> dict[str, str | bool]:
    """Debug endpoint: is tracing on, and where would traces show up.

    To view traces locally: run a Phoenix instance (e.g.
    `docker run -p 6006:6006 -p 4317:4317 arizephoenix/phoenix:latest` or
    `python -m phoenix.server.main serve`), set
    `PHOENIX_COLLECTOR_ENDPOINT` (e.g. `http://localhost:4318/v1/traces`)
    in `.env`, restart the backend, and open http://localhost:6006 — every
    node, LLM call, and guardrail check for a deal shows up as a nested
    span there.
    """
    return {
        "enabled": tracing.is_tracing_enabled(),
        "collector_endpoint": os.environ.get("PHOENIX_COLLECTOR_ENDPOINT") or "",
    }


@app.get("/inventory")
def list_inventory() -> list[InventoryItem]:
    """Debug/admin endpoint: list all inventory items."""
    return get_inventory_service().all_items()


@app.get("/inventory/{item_name}")
def get_inventory_item(item_name: str) -> InventoryItem:
    """Debug/admin endpoint: look up a single item by (fuzzy) name."""
    item = get_inventory_service().find(item_name)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
