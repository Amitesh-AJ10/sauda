"""Demo Controls panel triggers — deterministic, no real network calls."""

import pytest
from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.agent_commerce import get_orders
from app.api.whatsapp import get_conversations, get_graph
from app.main import app
from app.services.razorpay_client import Invoice, PaymentLink, get_razorpay_client
from app.services.whatsapp import get_whatsapp_service

client = TestClient(app)


class FakeGraph:
    """Mirrors the real graph's shape: negotiates straight to AWAITING_PAYMENT."""

    def invoke(self, state: DealState) -> dict:
        return {
            **state.model_dump(),
            "item_name": "Disposable Surgical Face Mask (Box of 50)",
            "qty": 500,
            "hospital_name": "City Care Hospital",
            "pin_code": "411001",
            "unit_price": 179.0,
            "status": DealStatus.AWAITING_PAYMENT,
            "payment_link_id": "plink_DEMO123",
            "payment_link_url": "https://rzp.io/i/DEMO123",
            "reply": "Please complete payment: https://rzp.io/i/DEMO123",
        }


class FakeWhatsAppService:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send_message(self, to: str, text: str) -> dict:
        self.sent.append((to, text))
        return {"messages": [{"id": "wamid.fake"}]}


class FakeRazorpay:
    def create_payment_link(self, amount_paise: int, description: str, notes: dict) -> PaymentLink:
        return PaymentLink(id="plink_AIBUYER", short_url="https://rzp.io/i/AIBUYER", status="created")

    def create_invoice(self, deal: DealState) -> Invoice:
        return Invoice(id="inv_DEMO123", short_url="https://rzp.io/i/invDEMO123", status="issued")


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_whatsapp_lead_trigger_creates_a_deal_via_the_real_graph():
    conversations: dict = {}
    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_graph] = lambda: FakeGraph()
    app.dependency_overrides[get_whatsapp_service] = lambda: FakeWhatsAppService()

    response = client.post("/api/v1/demo/whatsapp-lead")

    assert response.status_code == 200
    body = response.json()
    assert body["triggered"] == "whatsapp_lead"
    assert body["status"] == "awaiting_payment"
    assert body["deal_id"] in conversations


def test_guardrail_block_trigger_reports_the_forbidden_phrase_and_a_safe_reply():
    conversations: dict = {}
    app.dependency_overrides[get_conversations] = lambda: conversations

    response = client.post("/api/v1/demo/guardrail-block")

    assert response.status_code == 200
    body = response.json()
    assert body["triggered"] == "guardrail_block"
    assert "guarantee" in body["detail"].lower()
    stored = conversations[body["deal_id"]]
    assert stored.guardrail_violations
    assert "guarantee" not in stored.reply.lower()
    assert "warrant" not in stored.reply.lower()


def test_razorpay_payment_trigger_finalizes_the_most_recent_awaiting_deal():
    conversations = {
        "911111111111": DealState(
            item_name="Surgical Masks",
            qty=500,
            unit_price=179.0,
            status=DealStatus.AWAITING_PAYMENT,
            payment_link_id="plink_DEMO123",
            payment_link_url="https://rzp.io/i/DEMO123",
        )
    }
    fake_whatsapp = FakeWhatsAppService()
    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_orders] = lambda: {}
    app.dependency_overrides[get_razorpay_client] = lambda: FakeRazorpay()
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp

    response = client.post("/api/v1/demo/razorpay-payment")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispatched"
    assert conversations["911111111111"].status == DealStatus.DISPATCHED
    assert conversations["911111111111"].invoice_url == "https://rzp.io/i/invDEMO123"
    assert len(fake_whatsapp.sent) == 1


def test_razorpay_payment_trigger_404s_when_nothing_is_awaiting_payment():
    app.dependency_overrides[get_conversations] = lambda: {}
    app.dependency_overrides[get_orders] = lambda: {}

    response = client.post("/api/v1/demo/razorpay-payment")

    assert response.status_code == 404


def test_ai_buyer_purchase_trigger_creates_an_order():
    orders: dict = {}
    app.dependency_overrides[get_orders] = lambda: orders
    app.dependency_overrides[get_razorpay_client] = lambda: FakeRazorpay()

    response = client.post("/api/v1/demo/ai-buyer-purchase")

    assert response.status_code == 200
    body = response.json()
    assert body["triggered"] == "ai_buyer_purchase"
    assert body["status"] == "awaiting_payment"
    assert body["deal_id"] in orders
    assert orders[body["deal_id"]].payment_link_url == "https://rzp.io/i/AIBUYER"
