import hashlib
import hmac
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations
from app.main import app
from app.services.razorpay_client import Invoice, get_razorpay_client
from app.services.whatsapp import get_whatsapp_service

client = TestClient(app)

SECRET = "whsec_test123"


class FakeRazorpay:
    def __init__(self, invoice: Invoice | None = None, error: Exception | None = None):
        self._invoice = invoice or Invoice(
            id="inv_fake123", short_url="https://rzp.io/i/invfake123", status="issued"
        )
        self._error = error
        self.calls: list[DealState] = []

    def create_invoice(self, deal: DealState) -> Invoice:
        self.calls.append(deal)
        if self._error:
            raise self._error
        return self._invoice


class FakeWhatsAppService:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send_message(self, to: str, text: str) -> dict:
        self.sent.append((to, text))
        return {"messages": [{"id": "wamid.fake"}]}


def sign(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def paid_event(payment_link_id: str) -> bytes:
    return json.dumps(
        {
            "event": "payment_link.paid",
            "payload": {"payment_link": {"entity": {"id": payment_link_id}}},
        }
    ).encode()


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_valid_signature_and_paid_event_issues_invoice_notifies_buyer_and_dispatches(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)
    conversations = {
        "911234567890": DealState(
            status=DealStatus.AWAITING_PAYMENT,
            payment_link_id="plink_ABC123",
            item_name="Nitrile Examination Gloves",
            qty=50,
            unit_price=475.50,
        )
    }
    fake_razorpay = FakeRazorpay()
    fake_whatsapp = FakeWhatsAppService()
    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_razorpay_client] = lambda: fake_razorpay
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp

    body = paid_event("plink_ABC123")
    response = client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": sign(body)}
    )

    assert response.status_code == 200
    deal = conversations["911234567890"]
    assert deal.status == DealStatus.DISPATCHED
    assert deal.invoice_url == "https://rzp.io/i/invfake123"
    assert len(fake_razorpay.calls) == 1
    assert fake_whatsapp.sent == [("911234567890", deal.reply)]
    assert "https://rzp.io/i/invfake123" in fake_whatsapp.sent[0][1]


def test_invalid_signature_rejected_with_400(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)
    conversations = {
        "911234567890": DealState(status=DealStatus.AWAITING_PAYMENT, payment_link_id="plink_ABC123")
    }
    app.dependency_overrides[get_conversations] = lambda: conversations

    body = paid_event("plink_ABC123")
    response = client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": "wrong-signature"}
    )

    assert response.status_code == 400
    assert conversations["911234567890"].status == DealStatus.AWAITING_PAYMENT


def test_replayed_event_is_idempotent_noop(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)
    conversations = {
        "911234567890": DealState(status=DealStatus.AWAITING_PAYMENT, payment_link_id="plink_ABC123")
    }
    fake_razorpay = FakeRazorpay()
    fake_whatsapp = FakeWhatsAppService()
    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_razorpay_client] = lambda: fake_razorpay
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp

    body = paid_event("plink_ABC123")
    headers = {"X-Razorpay-Signature": sign(body)}

    first = client.post("/webhooks/razorpay", content=body, headers=headers)
    second = client.post("/webhooks/razorpay", content=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert conversations["911234567890"].status == DealStatus.DISPATCHED
    # invoice created exactly once and buyer notified exactly once, despite the replay
    assert len(fake_razorpay.calls) == 1
    assert len(fake_whatsapp.sent) == 1


def test_unknown_payment_link_id_is_ignored(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)
    conversations = {
        "911234567890": DealState(status=DealStatus.AWAITING_PAYMENT, payment_link_id="plink_ABC123")
    }
    app.dependency_overrides[get_conversations] = lambda: conversations

    body = paid_event("plink_DOES_NOT_EXIST")
    response = client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": sign(body)}
    )

    assert response.status_code == 200
    assert conversations["911234567890"].status == DealStatus.AWAITING_PAYMENT


def test_invoice_failure_does_not_mark_deal_dispatched(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)
    conversations = {
        "911234567890": DealState(status=DealStatus.AWAITING_PAYMENT, payment_link_id="plink_ABC123")
    }
    fake_razorpay = FakeRazorpay(error=httpx.HTTPStatusError("boom", request=None, response=None))
    fake_whatsapp = FakeWhatsAppService()
    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_razorpay_client] = lambda: fake_razorpay
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp

    body = paid_event("plink_ABC123")
    response = client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": sign(body)}
    )

    assert response.status_code == 200
    deal = conversations["911234567890"]
    assert deal.status == DealStatus.INVOICE_FAILED
    assert deal.status != DealStatus.DISPATCHED
    assert deal.invoice_url is None
    # buyer is never told the order shipped when the invoice call failed
    assert fake_whatsapp.sent == []
