"""One-click demo triggers behind the frontend's "Demo Controls" panel.

Not a customer-facing surface — these exist purely so a demo recording
doesn't need a terminal alongside the browser. Each one reuses the same
underlying logic the real integration paths use (guardrails, pricing,
Razorpay client, agent-commerce order creation); they just skip the
external preconditions a real caller can't fake on demand (a signed
Razorpay webhook body, an AI buyer's own API key) since the merchant
triggering these already *is* the authenticated party — this is their own
UI, not a public route.

Deliberately unauthenticated and in-memory, same caveat as the rest of the
buildathon-scope stores this reads from: fine for a demo, not for prod.
"""

import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agent.guardrails import check_text_guardrails, clamp_price, compute_unit_price
from app.agent.nodes import _safe_negotiation_reply
from app.agent.state import DealState, DealStatus
from app.api.agent_commerce import get_orders
from app.api.razorpay_webhooks import finalize_payment
from app.api.whatsapp import get_conversations, get_graph
from app.services.inventory import InventoryService, get_inventory_service
from app.services.razorpay_client import RazorpayClient, get_razorpay_client
from app.services.whatsapp import WhatsAppService, get_whatsapp_service

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])

# "Nitrile Examination Gloves" is unambiguous against the mock catalog
# (unlike e.g. "surgical face masks", which the LLM's free-text extraction
# can land on either the mask or the unrelated, much-lower-stock face
# shield SKU) — picked so the WhatsApp-lead demo trigger reliably runs the
# full happy path instead of gambling into an out-of-stock reply.
DEMO_LEAD_SENDER = "919800000001"
DEMO_LEAD_MESSAGES = [
    "Hi, we need 100 boxes of Nitrile Examination Gloves urgently for City Care Hospital.",
    "Our PIN code is 411001 — what's the best rate you can offer?",
]
DEMO_ITEM = "Nitrile Examination Gloves (Box of 100)"
DEMO_QTY = 100
DEMO_PIN = "411001"

# The forbidden phrase the guardrail is meant to catch — see
# app/agent/guardrails.py::FORBIDDEN_PATTERNS.
UNSAFE_DRAFT_REPLY = "Absolutely, we guarantee delivery in 10 minutes with a full warranty!"


class DemoTriggerResponse(BaseModel):
    triggered: Literal["whatsapp_lead", "guardrail_block", "razorpay_payment", "ai_buyer_purchase"]
    deal_id: str
    status: DealStatus
    detail: str


@router.post("/whatsapp-lead", response_model=DemoTriggerResponse)
def trigger_whatsapp_lead(
    conversations: dict[str, DealState] = Depends(get_conversations),
    graph=Depends(get_graph),
    whatsapp: WhatsAppService = Depends(get_whatsapp_service),
) -> DemoTriggerResponse:
    """Feed a canned inbound message through the *real* agent graph.

    A fresh demo sender each call (a counter suffix) so back-to-back clicks
    during a recording each show up as a new lead instead of resuming the
    same conversation.
    """
    sender = f"{DEMO_LEAD_SENDER}{int(time.time() * 1000) % 10000}"
    state = DealState()
    for message in DEMO_LEAD_MESSAGES:
        state.messages.append(message)
        try:
            result = graph.invoke(state)
            state = DealState(**result)
        except Exception:
            state.reply = "Sorry, we're having trouble processing that right now — we'll follow up shortly."
            break

    conversations[sender] = state
    if state.reply:
        try:
            whatsapp.send_message(sender, state.reply)
        except Exception:
            pass

    return DemoTriggerResponse(
        triggered="whatsapp_lead", deal_id=sender, status=state.status, detail=state.reply or ""
    )


@router.post("/guardrail-block", response_model=DemoTriggerResponse)
def trigger_guardrail_block(
    conversations: dict[str, DealState] = Depends(get_conversations),
    inventory: InventoryService = Depends(get_inventory_service),
) -> DemoTriggerResponse:
    """Run a deliberately unsafe draft reply through the real guardrail check.

    Demonstrates PRD §6 (no SLA/warranty promises) deterministically —
    doesn't depend on the LLM actually phrasing something unsafe on a given
    take, which isn't reliable enough to gamble a demo recording on.
    """
    item = inventory.find(DEMO_ITEM)
    unit_price = item.base_price if item else 0.0

    violations = check_text_guardrails(UNSAFE_DRAFT_REPLY)
    safe_reply = _safe_negotiation_reply(DEMO_ITEM, DEMO_QTY, unit_price, DealState())

    sender = f"{DEMO_LEAD_SENDER}-guardrail"
    state = DealState(
        item_name=DEMO_ITEM,
        qty=DEMO_QTY,
        unit_price=unit_price,
        status=DealStatus.NEGOTIATING,
        reply=safe_reply,
        guardrail_violations=violations,
    )
    conversations[sender] = state

    return DemoTriggerResponse(
        triggered="guardrail_block",
        deal_id=sender,
        status=state.status,
        detail=f"Blocked: {', '.join(violations)}. Rewrote to: {safe_reply}",
    )


@router.post("/razorpay-payment", response_model=DemoTriggerResponse)
def trigger_razorpay_payment(
    conversations: dict[str, DealState] = Depends(get_conversations),
    orders: dict[str, DealState] = Depends(get_orders),
    razorpay: RazorpayClient = Depends(get_razorpay_client),
    whatsapp: WhatsAppService = Depends(get_whatsapp_service),
) -> DemoTriggerResponse:
    """Simulate the `payment_link.paid` webhook for the most recent awaiting-payment deal."""
    for store, is_whatsapp in ((conversations, True), (orders, False)):
        candidates = [(k, s) for k, s in store.items() if s.status == DealStatus.AWAITING_PAYMENT]
        if candidates:
            key, state = candidates[-1]
            final_state = finalize_payment(
                key, state, store, is_whatsapp_deal=is_whatsapp, razorpay=razorpay, whatsapp=whatsapp
            )
            return DemoTriggerResponse(
                triggered="razorpay_payment",
                deal_id=key,
                status=final_state.status,
                detail=final_state.reply or "",
            )

    raise HTTPException(status_code=404, detail="No deal is currently awaiting payment")


@router.post("/ai-buyer-purchase", response_model=DemoTriggerResponse)
def trigger_ai_buyer_purchase(
    inventory: InventoryService = Depends(get_inventory_service),
    razorpay: RazorpayClient = Depends(get_razorpay_client),
    orders: dict[str, DealState] = Depends(get_orders),
) -> DemoTriggerResponse:
    """Same path as a real POST /api/v1/orders call from an AI buyer agent (Task 08) —
    called directly here since the merchant's own UI doesn't need its own AGENT_API_KEY."""
    item = inventory.find(DEMO_ITEM)
    if item is None or item.stock_qty <= 0:
        raise HTTPException(status_code=409, detail=f"'{DEMO_ITEM}' is out of stock")

    qty = min(DEMO_QTY, item.stock_qty)
    unit_price = clamp_price(compute_unit_price(item.base_price, qty), item.base_price)
    amount_paise = round(unit_price * qty * 100)

    link = razorpay.create_payment_link(
        amount_paise=amount_paise,
        description=f"{qty} x {item.item_name}",
        notes={"item_name": item.item_name, "hospital_name": "AI Buyer Corp", "pin_code": DEMO_PIN},
    )

    state = DealState(
        item_name=item.item_name,
        qty=qty,
        hospital_name="AI Buyer Corp",
        pin_code=DEMO_PIN,
        unit_price=unit_price,
        available_qty=item.stock_qty,
        status=DealStatus.AWAITING_PAYMENT,
        payment_link_id=link.id,
        payment_link_url=link.short_url,
    )
    orders[link.id] = state

    return DemoTriggerResponse(
        triggered="ai_buyer_purchase",
        deal_id=link.id,
        status=state.status,
        detail=f"AI buyer ordered {qty} x {item.item_name} — payment link created.",
    )
