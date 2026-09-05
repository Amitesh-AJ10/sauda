"""Machine-readable REST API for AI buyer agents (Track 01 mandate).

A hospital's own procurement agent can fetch a quote and pay without ever
going through a WhatsApp conversation. Reuses the same deterministic
pricing (`app/agent/guardrails.py`) and Razorpay integration
(`app/services/razorpay_client.py`) the WhatsApp flow uses — a
fully-specified request never touches `services/llm.py`.

Orders are kept in their own in-memory store, keyed by the Razorpay payment
link id (so it doubles as `order_id`). `app/api/razorpay_webhooks.py` polls
this store alongside the WhatsApp conversation store when a payment comes
in, so `GET /orders/{order_id}` reflects the same status transitions the
webhook drives.
"""

import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.agent.guardrails import clamp_price, compute_unit_price
from app.agent.state import DealState, DealStatus
from app.services.inventory import InventoryService, get_inventory_service
from app.services.razorpay_client import RazorpayClient, get_razorpay_client

# One in-memory order per created payment link, for the life of the process
# — same "swap for a real datastore before this goes past a demo" caveat as
# the WhatsApp conversation store in app/api/whatsapp.py.
_orders: dict[str, DealState] = {}


def get_orders() -> dict[str, DealState]:
    return _orders


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """Static API key check — enough to prevent open abuse, not a full auth system."""
    expected = os.environ.get("AGENT_API_KEY")
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key")


router = APIRouter(prefix="/api/v1", tags=["agent-commerce"], dependencies=[Depends(require_api_key)])


class QuoteRequest(BaseModel):
    item_name: str
    qty: int = Field(gt=0)
    pin_code: str


class QuoteResponse(BaseModel):
    available_qty: int
    unit_price: float
    total_price: float
    currency: str = "INR"


@router.post("/quote", response_model=QuoteResponse)
def create_quote(
    request: QuoteRequest, inventory: InventoryService = Depends(get_inventory_service)
) -> QuoteResponse:
    """Deterministic quote, no LLM round-trip: same pricing math as `negotiate`."""
    item = inventory.find(request.item_name)
    if item is None:
        raise HTTPException(status_code=404, detail=f"'{request.item_name}' is not in stock")

    # Never invent stock: an over-stock request is quoted for what's
    # actually available, not silently rejected.
    quoted_qty = min(request.qty, item.stock_qty)
    unit_price = clamp_price(compute_unit_price(item.base_price, quoted_qty), item.base_price)

    return QuoteResponse(
        available_qty=item.stock_qty,
        unit_price=unit_price,
        total_price=round(unit_price * quoted_qty, 2),
    )


class OrderRequest(BaseModel):
    item_name: str
    qty: int = Field(gt=0)
    pin_code: str
    hospital_name: str | None = None


class OrderResponse(BaseModel):
    order_id: str
    payment_link_url: str
    status: DealStatus


@router.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(
    request: OrderRequest,
    inventory: InventoryService = Depends(get_inventory_service),
    razorpay: RazorpayClient = Depends(get_razorpay_client),
    orders: dict[str, DealState] = Depends(get_orders),
) -> OrderResponse:
    """Confirm a quote: create a real Razorpay payment link, same as the WhatsApp flow."""
    item = inventory.find(request.item_name)
    if item is None:
        raise HTTPException(status_code=404, detail=f"'{request.item_name}' is not in stock")
    if item.stock_qty <= 0:
        raise HTTPException(status_code=409, detail=f"'{item.item_name}' is out of stock")

    qty = min(request.qty, item.stock_qty)
    unit_price = clamp_price(compute_unit_price(item.base_price, qty), item.base_price)
    amount_paise = round(unit_price * qty * 100)

    link = razorpay.create_payment_link(
        amount_paise=amount_paise,
        description=f"{qty} x {item.item_name}",
        notes={
            "item_name": item.item_name,
            "hospital_name": request.hospital_name or "",
            "pin_code": request.pin_code,
        },
    )

    state = DealState(
        item_name=item.item_name,
        qty=qty,
        hospital_name=request.hospital_name,
        pin_code=request.pin_code,
        unit_price=unit_price,
        available_qty=item.stock_qty,
        status=DealStatus.AWAITING_PAYMENT,
        payment_link_id=link.id,
        payment_link_url=link.short_url,
    )
    orders[link.id] = state

    return OrderResponse(order_id=link.id, payment_link_url=link.short_url, status=state.status)


class OrderStatusResponse(BaseModel):
    order_id: str
    status: DealStatus
    invoice_url: str | None = None


@router.get("/orders/{order_id}", response_model=OrderStatusResponse)
def get_order(order_id: str, orders: dict[str, DealState] = Depends(get_orders)) -> OrderStatusResponse:
    """Poll for status: updated in place by the Razorpay webhook once paid."""
    state = orders.get(order_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderStatusResponse(order_id=order_id, status=state.status, invoice_url=state.invoice_url)
