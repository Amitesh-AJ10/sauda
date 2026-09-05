"""Hospital-facing chat: the real agent graph, addressed by hospital id.

Same graph, same conversation store, same guardrails as the WhatsApp
webhook (`app/api/whatsapp.py`) — this just lets the frontend's per-hospital
chat page drive a turn directly over plain HTTP instead of needing a
Meta-shaped webhook payload. Nothing here is simulated: real LLM calls,
real inventory lookup, real Razorpay payment links.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agent import nodes
from app.agent.audit import build_audit_trail
from app.agent.state import DealState, DealStatus
from app.api.razorpay_webhooks import finalize_payment
from app.api.whatsapp import get_conversations, get_graph
from app.data.hospitals import Hospital, get_hospital, list_hospitals
from app.services.razorpay_client import RazorpayClient, get_razorpay_client
from app.services.whatsapp import WhatsAppService, get_whatsapp_service

logger = logging.getLogger(__name__)

hospitals_router = APIRouter(prefix="/api/v1", tags=["hospitals"])
chat_router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Once a deal has real payment machinery in motion, a stray chat message
# must never be allowed to restart extract_intent/negotiate from scratch —
# that used to silently reset the status back to NEGOTIATING and re-quote
# the whole offer, discarding the fact that a payment link already exists.
# (OUT_OF_STOCK/DECLINED are deliberately *not* here — a follow-up like
# "what about a different item" should still flow through the graph normally.)
_LOCKED_STATUSES = {
    DealStatus.AWAITING_PAYMENT,
    DealStatus.PAID,
    DealStatus.ISSUING_INVOICE,
    DealStatus.DISPATCHED,
    DealStatus.INVOICE_FAILED,
}


@hospitals_router.get("/hospitals", response_model=list[Hospital])
def get_hospitals() -> list[Hospital]:
    return list_hospitals()


class ChatMessageRequest(BaseModel):
    text: str = Field(min_length=1)


class ChatMessageResponse(BaseModel):
    id: str
    status: str
    reply: str | None = None
    messages: list[str] = Field(default_factory=list)
    payment_link_url: str | None = None
    invoice_url: str | None = None
    guardrail_violations: list[str] = Field(default_factory=list)
    audit_trail: list[str] = Field(default_factory=list)


def _handle_locked_state(
    hospital_id: str,
    state: DealState,
    conversations: dict[str, DealState],
    razorpay: RazorpayClient,
    whatsapp: WhatsAppService,
) -> DealState:
    """A message that arrives once the deal is already past negotiation.

    If it's awaiting payment, actually ask Razorpay's real API whether it's
    been paid — "payment done" gets checked for real right here instead of
    waiting for the next dashboard poll, and instead of being ignored. If
    it isn't paid yet (or the deal's already finished one way or another),
    give an honest status reply without touching item/qty/price/status —
    never restart the negotiation for a stray follow-up message.
    """
    last_message = state.messages[-1] if state.messages else ""

    if state.status == DealStatus.AWAITING_PAYMENT and state.payment_link_id:
        try:
            if razorpay.get_payment_link_status(state.payment_link_id) == "paid":
                return finalize_payment(
                    hospital_id, state, conversations, is_whatsapp_deal=True, razorpay=razorpay, whatsapp=whatsapp
                )
        except Exception:
            logger.exception("Failed to check Razorpay payment status for %s", hospital_id)
            return state.model_copy(
                update={
                    "reply": "We're having trouble confirming that on our end right now — "
                    "please try again in a moment, or use the payment link above."
                }
            )

        if nodes.is_payment_claim(last_message):
            reply = (
                "I don't see that payment reflected on our end yet — please complete it via "
                "the link above, or give it a moment and I'll check again."
            )
        else:
            reply = f"Your order is awaiting payment — here's the link again: {state.payment_link_url}"
        return state.model_copy(update={"reply": reply})

    status_replies = {
        DealStatus.PAID: "Payment received — your GST invoice is being generated now.",
        DealStatus.ISSUING_INVOICE: "Payment received — your GST invoice is being generated now.",
        DealStatus.DISPATCHED: (
            f"This order's already paid and dispatched! Your invoice: {state.invoice_url}"
            if state.invoice_url
            else "This order's already paid and dispatched!"
        ),
        DealStatus.INVOICE_FAILED: "Payment was received, but invoice generation hit an error — we're looking into it.",
    }
    return state.model_copy(update={"reply": status_replies.get(state.status, state.reply)})


@chat_router.post("/{hospital_id}/messages", response_model=ChatMessageResponse)
def send_chat_message(
    hospital_id: str,
    request: ChatMessageRequest,
    conversations: dict[str, DealState] = Depends(get_conversations),
    graph=Depends(get_graph),
    razorpay: RazorpayClient = Depends(get_razorpay_client),
    whatsapp: WhatsAppService = Depends(get_whatsapp_service),
) -> ChatMessageResponse:
    hospital = get_hospital(hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail=f"Unknown hospital '{hospital_id}'")

    # First message from this hospital: seed hospital_name/pin_code from the
    # directory (a repeat B2B buyer, not a stranger) so the agent doesn't
    # need to ask for logistics info it already has on file.
    state = conversations.get(hospital_id) or DealState(hospital_name=hospital.name, pin_code=hospital.pin_code)
    state.messages.append(request.text)

    if state.status in _LOCKED_STATUSES:
        new_state = _handle_locked_state(hospital_id, state, conversations, razorpay, whatsapp)
    else:
        try:
            result = graph.invoke(state)
            new_state = DealState(**result)
        except Exception:
            logger.exception("Agent graph failed for hospital %s", hospital_id)
            state.reply = "Sorry, we're having trouble processing that right now — we'll follow up shortly."
            new_state = state

    conversations[hospital_id] = new_state

    return ChatMessageResponse(
        id=hospital_id,
        status=new_state.status,
        reply=new_state.reply,
        messages=new_state.messages,
        payment_link_url=new_state.payment_link_url,
        invoice_url=new_state.invoice_url,
        guardrail_violations=new_state.guardrail_violations,
        audit_trail=build_audit_trail(new_state),
    )
