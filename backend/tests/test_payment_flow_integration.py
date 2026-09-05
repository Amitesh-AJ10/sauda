"""End-to-end: negotiate -> payment link created -> webhook -> Paid.

Runs the real LangGraph graph (with a fake LLM and a fake Razorpay client —
no network calls) through both webhooks, exactly as production wiring would.
"""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.agent.graph import build_graph
from app.agent.state import DealState, DealStatus, ExtractedIntent
from app.api.whatsapp import get_conversations, get_graph
from app.main import app
from app.services.inventory import InventoryService
from app.services.razorpay_client import PaymentLink
from app.services.whatsapp import get_whatsapp_service

client = TestClient(app)
SECRET = "whsec_test123"


class FakeLLM:
    def __init__(self, structured: ExtractedIntent, text: str):
        self._structured = structured
        self._text = text

    def complete_structured(self, system, user, schema):
        return self._structured

    def complete_text(self, system, user):
        return self._text


class FakeRazorpay:
    def __init__(self):
        self.calls: list[tuple[int, str, dict]] = []

    def create_payment_link(self, amount_paise: int, description: str, notes: dict) -> PaymentLink:
        self.calls.append((amount_paise, description, notes))
        return PaymentLink(id="plink_INTEG123", short_url="https://rzp.io/i/INTEG123", status="created")


class FakeWhatsAppService:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send_message(self, to: str, text: str) -> dict:
        self.sent.append((to, text))
        return {"messages": [{"id": "wamid.fake"}]}


def inbound_payload(sender: str, text: str) -> dict:
    return {
        "entry": [
            {"changes": [{"value": {"messages": [{"from": sender, "type": "text", "text": {"body": text}}]}}]}
        ]
    }


def sign(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_negotiate_to_paid_full_flow(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)

    graph = build_graph(
        inventory=InventoryService(),
        llm=FakeLLM(
            structured=ExtractedIntent(
                item_name="Nitrile Examination Gloves",
                qty=50,
                hospital_name="City Hospital",
                pin_code="411001",
            ),
            text="We can offer 50 boxes at a fair rate. We will dispatch via our logistics partner post-payment.",
        ),
        razorpay=FakeRazorpay(),
    )
    fake_whatsapp = FakeWhatsAppService()
    conversations: dict[str, DealState] = {}

    app.dependency_overrides[get_graph] = lambda: graph
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp
    app.dependency_overrides[get_conversations] = lambda: conversations

    # 1. Buyer negotiates -> graph runs through to (stubbed) dispatch, but
    #    along the way a real payment link gets created.
    sender = "911234567890"
    response = client.post(
        "/webhooks/whatsapp", json=inbound_payload(sender, "Need 50 nitrile gloves, best rate?")
    )
    assert response.status_code == 200
    assert conversations[sender].payment_link_id == "plink_INTEG123"
    assert conversations[sender].payment_link_url == "https://rzp.io/i/INTEG123"

    # 2. Razorpay confirms payment via webhook -> deal transitions to Paid.
    body = json.dumps(
        {
            "event": "payment_link.paid",
            "payload": {"payment_link": {"entity": {"id": "plink_INTEG123"}}},
        }
    ).encode()
    webhook_response = client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": sign(body)}
    )

    assert webhook_response.status_code == 200
    assert conversations[sender].status == DealStatus.PAID

    # 3. Replaying the same event is a no-op.
    replay_response = client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": sign(body)}
    )
    assert replay_response.status_code == 200
    assert conversations[sender].status == DealStatus.PAID
