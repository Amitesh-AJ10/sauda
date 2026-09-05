"""Inbound Razorpay webhook: verifies the signature, closes the loop.

`payment_link.paid` -> deal marked `Paid` -> GST invoice generated -> invoice
link pushed to the buyer on WhatsApp -> deal marked `Dispatched`, all
synchronously, with zero manual merchant input (PRD F7/F8).

Deals are looked up by `payment_link_id` across both in-memory stores a
payment link can originate from: the WhatsApp conversation store (see
app/api/whatsapp.py) and the AI-buyer-agent order store (see
app/api/agent_commerce.py) — fine for the buildathon scope, not durable
across restarts. Only a WhatsApp-originated deal gets a WhatsApp
notification; an agent order is expected to poll `GET /api/v1/orders/{id}`
instead.
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request

from app.agent import nodes
from app.agent.state import DealState, DealStatus
from app.api.agent_commerce import get_orders
from app.api.whatsapp import get_conversations
from app.observability.tracing import traced_node
from app.services.razorpay_client import RazorpayClient, get_razorpay_client, verify_webhook_signature
from app.services.whatsapp import WhatsAppService, get_whatsapp_service

logger = logging.getLogger(__name__)

router = APIRouter()


def _find_by_payment_link_id(
    store: dict[str, DealState], payment_link_id: str
) -> tuple[str, DealState] | None:
    for key, state in store.items():
        if state.payment_link_id == payment_link_id:
            return key, state
    return None


def finalize_payment(
    key: str,
    state: DealState,
    store: dict[str, DealState],
    is_whatsapp_deal: bool,
    razorpay: RazorpayClient,
    whatsapp: WhatsAppService,
) -> DealState:
    """Paid -> invoice issued -> dispatched, and (for a WhatsApp deal) notify the buyer.

    Shared by the real `payment_link.paid` webhook above and by the demo
    "Trigger Razorpay Webhook" control (`app/api/demo.py`) — same effect,
    the demo control just skips signature verification and payload lookup.
    """
    if state.status == DealStatus.DISPATCHED:
        return state  # already processed — idempotent no-op on replay

    paid_state = state.model_copy(update={"status": DealStatus.PAID})
    updates = traced_node("issue_invoice")(nodes.issue_invoice)(paid_state, razorpay=razorpay)
    final_state = paid_state.model_copy(update=updates)
    store[key] = final_state

    if is_whatsapp_deal and final_state.status == DealStatus.DISPATCHED and final_state.reply:
        try:
            whatsapp.send_message(key, final_state.reply)
        except Exception:
            # Same rationale as app/api/whatsapp.py: a delivery failure (no
            # real WhatsApp Cloud API creds in this environment) shouldn't
            # fail the payment finalization that already succeeded — the
            # invoice is issued and the deal is dispatched either way.
            logger.exception("Failed to deliver WhatsApp invoice notice to %s", key)

    return final_state


@router.post("/webhooks/razorpay")
async def receive_webhook(
    request: Request,
    conversations: dict[str, DealState] = Depends(get_conversations),
    orders: dict[str, DealState] = Depends(get_orders),
    razorpay: RazorpayClient = Depends(get_razorpay_client),
    whatsapp: WhatsAppService = Depends(get_whatsapp_service),
):
    body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

    if not verify_webhook_signature(body, signature, secret):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    if payload.get("event") != "payment_link.paid":
        return {"status": "ignored"}

    payment_link_id = (
        payload.get("payload", {}).get("payment_link", {}).get("entity", {}).get("id")
    )
    if not payment_link_id:
        return {"status": "ignored"}

    store = conversations
    match = _find_by_payment_link_id(store, payment_link_id)
    if match is None:
        store = orders
        match = _find_by_payment_link_id(store, payment_link_id)
    if match is None:
        return {"status": "ignored"}

    key, state = match
    finalize_payment(
        key, state, store, is_whatsapp_deal=store is conversations, razorpay=razorpay, whatsapp=whatsapp
    )
    return {"status": "ok"}
