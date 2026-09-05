"""End-to-end: negotiate -> payment link created -> webhook -> invoice -> Dispatched.

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
from app.services.razorpay_client import Invoice, PaymentLink, get_razorpay_client
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
        self.payment_link_calls: list[tuple[int, str, dict]] = []
        self.invoice_calls: list[DealState] = []

    def create_payment_link(self, amount_paise: int, description: str, notes: dict) -> PaymentLink:
        self.payment_link_calls.append((amount_paise, description, notes))
        return PaymentLink(id="plink_INTEG123", short_url="https://rzp.io/i/INTEG123", status="created")

    def create_invoice(self, deal: DealState) -> Invoice:
        self.invoice_calls.append(deal)
        return Invoice(id="inv_INTEG123", short_url="https://rzp.io/i/invINTEG123", status="issued")


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


def test_negotiate_to_paid_to_invoiced_full_flow(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)

    fake_razorpay = FakeRazorpay()
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
        razorpay=fake_razorpay,
    )
    fake_whatsapp = FakeWhatsAppService()
    conversations: dict[str, DealState] = {}

    app.dependency_overrides[get_graph] = lambda: graph
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp
    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_razorpay_client] = lambda: fake_razorpay

    # 1. Buyer negotiates -> graph stops at NEGOTIATING and asks whether to
    #    send the payment link — no link exists yet.
    sender = "911234567890"
    response = client.post(
        "/webhooks/whatsapp", json=inbound_payload(sender, "Need 50 nitrile gloves, best rate?")
    )
    assert response.status_code == 200
    assert conversations[sender].status == DealStatus.NEGOTIATING
    assert conversations[sender].payment_link_id is None

    # 1b. Only an explicit confirmation creates the real payment link.
    response = client.post("/webhooks/whatsapp", json=inbound_payload(sender, "Yes, go ahead"))
    assert response.status_code == 200
    assert conversations[sender].status == DealStatus.AWAITING_PAYMENT
    assert conversations[sender].payment_link_id == "plink_INTEG123"
    assert conversations[sender].payment_link_url == "https://rzp.io/i/INTEG123"
    assert len(fake_whatsapp.sent) == 2  # negotiation message, then the payment-link message

    # 2. Razorpay confirms payment via webhook -> invoice generated, buyer
    #    notified on WhatsApp with the invoice link, deal Dispatched.
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
    assert conversations[sender].status == DealStatus.DISPATCHED
    assert conversations[sender].invoice_url == "https://rzp.io/i/invINTEG123"
    assert len(fake_razorpay.invoice_calls) == 1
    assert len(fake_whatsapp.sent) == 3  # negotiation, payment-link, then invoice message
    assert fake_whatsapp.sent[2][0] == sender
    assert "https://rzp.io/i/invINTEG123" in fake_whatsapp.sent[2][1]

    # 3. Replaying the same event is a no-op: no duplicate invoice, no duplicate message.
    replay_response = client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": sign(body)}
    )
    assert replay_response.status_code == 200
    assert conversations[sender].status == DealStatus.DISPATCHED
    assert len(fake_razorpay.invoice_calls) == 1
    assert len(fake_whatsapp.sent) == 3
