"""Inbound/outbound WhatsApp webhook, wired to the LangGraph agent graph.

Conversation state is an in-memory dict keyed by sender phone number — fine
for the buildathon scope, not durable across restarts (see README).
"""

import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse

from app.agent.graph import get_compiled_graph
from app.agent.state import DealState
from app.services.whatsapp import WhatsAppService, get_whatsapp_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level singleton: one deal per sender phone number, for the life of
# the process. Swap for a real datastore before this goes past a demo.
_conversations: dict[str, DealState] = {}


def get_conversations() -> dict[str, DealState]:
    return _conversations


def get_graph():
    return get_compiled_graph()


@router.get("/webhooks/whatsapp")
def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """Meta's verification handshake: echo the challenge iff the token matches."""
    expected_token = os.environ.get("WHATSAPP_VERIFY_TOKEN")
    if hub_mode == "subscribe" and expected_token and hub_verify_token == expected_token:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification token mismatch")


def _extract_inbound_message(payload: dict) -> tuple[str, str] | None:
    """Pull (sender, text) out of a WhatsApp Cloud API webhook payload.

    Returns None for anything that isn't an inbound text message (status
    updates, media messages, malformed payloads) — those are ignored.
    """
    try:
        value = payload["entry"][0]["changes"][0]["value"]
        messages = value.get("messages")
        if not messages:
            return None
        message = messages[0]
        return message["from"], message.get("text", {}).get("body", "")
    except (KeyError, IndexError, TypeError):
        return None


@router.post("/webhooks/whatsapp")
def receive_webhook(
    payload: dict,
    conversations: dict[str, DealState] = Depends(get_conversations),
    graph=Depends(get_graph),
    whatsapp: WhatsAppService = Depends(get_whatsapp_service),
):
    parsed = _extract_inbound_message(payload)
    if parsed is None:
        return {"status": "ignored"}

    sender, text = parsed
    state = conversations.get(sender) or DealState()
    state.messages.append(text)

    try:
        result = graph.invoke(state)
        new_state = DealState(**result)
    except Exception:
        # LLM/network hiccups (rate limits, timeouts, ...) shouldn't crash
        # the webhook — keep the conversation resumable and let the buyer
        # know we're still on it, rather than 500ing back to Meta.
        logger.exception("Agent graph failed for sender %s", sender)
        state.reply = "Sorry, we're having trouble processing that right now — we'll follow up shortly."
        new_state = state

    conversations[sender] = new_state

    if new_state.reply:
        try:
            whatsapp.send_message(sender, new_state.reply)
        except Exception:
            # Delivery failure (e.g. no real WhatsApp Cloud API creds in
            # this environment) shouldn't crash the webhook either — the
            # reply is still visible via GET /api/v1/deals.
            logger.exception("Failed to deliver WhatsApp reply to %s", sender)

    return {"status": "ok"}
