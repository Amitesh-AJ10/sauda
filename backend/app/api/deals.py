"""Lightweight read-only deal list for the frontend map UI (Task 09) to poll.

Sourced from the same in-memory WhatsApp conversation store `whatsapp.py`
already keeps — one entry per sender phone number. Deals created through
the agent-commerce API (`app/api/agent_commerce.py`) aren't included here:
that store has no inbound-lead concept (an order starts at
`AWAITING_PAYMENT`), which is out of scope for this task's Hospital
lead/payment indicators.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations

router = APIRouter(prefix="/api/v1", tags=["deals"])


class DealSummary(BaseModel):
    id: str
    hospital_name: str | None = None
    item_name: str | None = None
    qty: int | None = None
    status: DealStatus
    payment_link_url: str | None = None
    invoice_url: str | None = None
    messages: list[str] = Field(default_factory=list)
    reply: str | None = None
    guardrail_violations: list[str] = Field(default_factory=list)


@router.get("/deals", response_model=list[DealSummary])
def list_deals(conversations: dict[str, DealState] = Depends(get_conversations)) -> list[DealSummary]:
    return [
        DealSummary(
            id=sender,
            hospital_name=state.hospital_name,
            item_name=state.item_name,
            qty=state.qty,
            status=state.status,
            payment_link_url=state.payment_link_url,
            invoice_url=state.invoice_url,
            messages=state.messages,
            reply=state.reply,
            guardrail_violations=state.guardrail_violations,
        )
        for sender, state in conversations.items()
    ]
