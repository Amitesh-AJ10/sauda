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

from app.agent.audit import build_audit_trail
from app.agent.state import DealState
from app.api.whatsapp import get_conversations, get_graph
from app.data.hospitals import Hospital, get_hospital, list_hospitals

logger = logging.getLogger(__name__)

hospitals_router = APIRouter(prefix="/api/v1", tags=["hospitals"])
chat_router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


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


@chat_router.post("/{hospital_id}/messages", response_model=ChatMessageResponse)
def send_chat_message(
    hospital_id: str,
    request: ChatMessageRequest,
    conversations: dict[str, DealState] = Depends(get_conversations),
    graph=Depends(get_graph),
) -> ChatMessageResponse:
    hospital = get_hospital(hospital_id)
    if hospital is None:
        raise HTTPException(status_code=404, detail=f"Unknown hospital '{hospital_id}'")

    # First message from this hospital: seed hospital_name/pin_code from the
    # directory (a repeat B2B buyer, not a stranger) so the agent doesn't
    # need to ask for logistics info it already has on file.
    state = conversations.get(hospital_id) or DealState(hospital_name=hospital.name, pin_code=hospital.pin_code)
    state.messages.append(request.text)

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
