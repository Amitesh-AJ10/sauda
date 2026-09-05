import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations
from app.main import app

client = TestClient(app)

SECRET = "whsec_test123"


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


def test_valid_signature_and_paid_event_transitions_deal_to_paid(monkeypatch):
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", SECRET)
    conversations = {
        "911234567890": DealState(status=DealStatus.AWAITING_PAYMENT, payment_link_id="plink_ABC123")
    }
    app.dependency_overrides[get_conversations] = lambda: conversations

    body = paid_event("plink_ABC123")
    response = client.post(
        "/webhooks/razorpay", content=body, headers={"X-Razorpay-Signature": sign(body)}
    )

    assert response.status_code == 200
    assert conversations["911234567890"].status == DealStatus.PAID


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
    app.dependency_overrides[get_conversations] = lambda: conversations

    body = paid_event("plink_ABC123")
    headers = {"X-Razorpay-Signature": sign(body)}

    first = client.post("/webhooks/razorpay", content=body, headers=headers)
    second = client.post("/webhooks/razorpay", content=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert conversations["911234567890"].status == DealStatus.PAID


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
