"""Read-only deal list for the frontend to poll — the merchant dashboard's
single source of truth.

Sourced from the same in-memory conversation store `whatsapp.py`/`chat.py`
share (one entry per hospital id or WhatsApp phone number). Always includes
every hardcoded hospital (see `app/data/hospitals.py`), even ones that
haven't messaged yet, so the dashboard has a stable set of tiles.

Also doubles as the payment-confirmation loop: since local dev has no
public URL for Razorpay's webhook to call, every poll asks Razorpay's real
API whether any awaiting-payment deal has actually been paid, and finalizes
it (issues the invoice, marks dispatched) the moment it has — genuinely
checked, never simulated.
"""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.agent.audit import build_audit_trail
from app.agent.state import DealState, DealStatus
from app.api.razorpay_webhooks import finalize_payment
from app.api.whatsapp import get_conversations
from app.data.hospitals import list_hospitals
from app.services.razorpay_client import RazorpayClient, get_razorpay_client
from app.services.whatsapp import WhatsAppService, get_whatsapp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["deals"])


class DealSummary(BaseModel):
    id: str
    hospital_name: str | None = None
    item_name: str | None = None
    qty: int | None = None
    status: DealStatus | None = None
    payment_link_url: str | None = None
    invoice_url: str | None = None
    messages: list[str] = Field(default_factory=list)
    reply: str | None = None
    guardrail_violations: list[str] = Field(default_factory=list)
    audit_trail: list[str] = Field(default_factory=list)


def _reconcile_payments(
    conversations: dict[str, DealState], razorpay: RazorpayClient, whatsapp: WhatsAppService
) -> None:
    """Ask Razorpay whether any awaiting-payment deal has actually been paid."""
    for key, state in list(conversations.items()):
        if state.status != DealStatus.AWAITING_PAYMENT or not state.payment_link_id:
            continue
        try:
            if razorpay.get_payment_link_status(state.payment_link_id) == "paid":
                conversations[key] = finalize_payment(
                    key, state, conversations, is_whatsapp_deal=True, razorpay=razorpay, whatsapp=whatsapp
                )
        except Exception:
            # Network hiccup or missing/placeholder Razorpay creds — leave the
            # deal awaiting payment, try again on the next poll.
            logger.exception("Failed to check Razorpay payment status for %s", key)


def _summary(deal_id: str, fallback_hospital_name: str | None, state: DealState | None) -> DealSummary:
    if state is None:
        return DealSummary(id=deal_id, hospital_name=fallback_hospital_name)
    return DealSummary(
        id=deal_id,
        hospital_name=state.hospital_name or fallback_hospital_name,
        item_name=state.item_name,
        qty=state.qty,
        status=state.status,
        payment_link_url=state.payment_link_url,
        invoice_url=state.invoice_url,
        messages=state.messages,
        reply=state.reply,
        guardrail_violations=state.guardrail_violations,
        audit_trail=build_audit_trail(state),
    )


@router.get("/deals", response_model=list[DealSummary])
def list_deals(
    conversations: dict[str, DealState] = Depends(get_conversations),
    razorpay: RazorpayClient = Depends(get_razorpay_client),
    whatsapp: WhatsAppService = Depends(get_whatsapp_service),
) -> list[DealSummary]:
    _reconcile_payments(conversations, razorpay, whatsapp)

    hospitals = list_hospitals()
    result = [_summary(hospital.id, hospital.name, conversations.get(hospital.id)) for hospital in hospitals]

    known_ids = {hospital.id for hospital in hospitals}
    for key, state in conversations.items():
        if key in known_ids:
            continue
        result.append(_summary(key, state.hospital_name, state))

    return result
