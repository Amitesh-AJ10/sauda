"""Inbound Razorpay webhook: verifies the signature, closes the loop.

`payment_link.paid` -> deal marked `Paid` -> GST invoice generated -> invoice
link pushed to the buyer on WhatsApp -> deal marked `Dispatched`, all
synchronously, with zero manual merchant input (PRD F7/F8).

Deals are looked up by `payment_link_id` across the same in-memory
conversation store the WhatsApp webhook writes to (see app/api/whatsapp.py)
— fine for the buildathon scope, not durable across restarts.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request

from app.agent import nodes
from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations
from app.observability.tracing import traced_node
from app.services.razorpay_client import RazorpayClient, get_razorpay_client, verify_webhook_signature
from app.services.whatsapp import WhatsAppService, get_whatsapp_service

router = APIRouter()


def _find_by_payment_link_id(
    conversations: dict[str, DealState], payment_link_id: str
) -> tuple[str, DealState] | None:
    for sender, state in conversations.items():
        if state.payment_link_id == payment_link_id:
            return sender, state
    return None


@router.post("/webhooks/razorpay")
async def receive_webhook(
    request: Request,
    conversations: dict[str, DealState] = Depends(get_conversations),
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

    match = _find_by_payment_link_id(conversations, payment_link_id)
    if match is None:
        return {"status": "ignored"}

    sender, state = match
    if state.status == DealStatus.DISPATCHED:
        return {"status": "ok"}  # already processed — idempotent no-op on replay

    paid_state = state.model_copy(update={"status": DealStatus.PAID})
    updates = traced_node("issue_invoice")(nodes.issue_invoice)(paid_state, razorpay=razorpay)
    final_state = paid_state.model_copy(update=updates)
    conversations[sender] = final_state

    if final_state.status == DealStatus.DISPATCHED and final_state.reply:
        whatsapp.send_message(sender, final_state.reply)

    return {"status": "ok"}
