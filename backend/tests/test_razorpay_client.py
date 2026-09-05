import httpx
import pytest

from app.agent.state import DealState
from app.services.razorpay_client import RazorpayClient, verify_webhook_signature


class FakeResponse:
    def __init__(self, json_body: dict, status_code: int = 200):
        self._json_body = json_body
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self):
        return self._json_body


# --- create_payment_link ---------------------------------------------------


def test_create_payment_link_sends_correct_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, auth, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["auth"] = auth
        return FakeResponse(
            {"id": "plink_ABC123", "short_url": "https://rzp.io/i/ABC123", "status": "created"}
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    client = RazorpayClient(key_id="rzp_test_key", key_secret="rzp_test_secret")
    link = client.create_payment_link(
        amount_paise=237750,
        description="50 x Nitrile Examination Gloves",
        notes={"hospital_name": "City Hospital"},
    )

    assert captured["url"] == "https://api.razorpay.com/v1/payment_links"
    assert captured["json"] == {
        "amount": 237750,
        "currency": "INR",
        "description": "50 x Nitrile Examination Gloves",
        "notes": {"hospital_name": "City Hospital"},
    }
    assert captured["auth"] == ("rzp_test_key", "rzp_test_secret")
    assert link.id == "plink_ABC123"
    assert link.short_url == "https://rzp.io/i/ABC123"
    assert link.status == "created"


# --- create_invoice ---------------------------------------------------------


def test_create_invoice_sends_correct_line_items_and_amount(monkeypatch):
    captured = {}

    def fake_post(url, json, auth, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["auth"] = auth
        return FakeResponse(
            {"id": "inv_ABC123", "short_url": "https://rzp.io/i/invABC123", "status": "issued"}
        )

    monkeypatch.setattr(httpx, "post", fake_post)

    client = RazorpayClient(key_id="rzp_test_key", key_secret="rzp_test_secret")
    deal = DealState(
        item_name="Nitrile Examination Gloves",
        qty=50,
        unit_price=475.50,
        hospital_name="City Hospital",
        pin_code="411001",
    )
    invoice = client.create_invoice(deal)

    assert captured["url"] == "https://api.razorpay.com/v1/invoices"
    assert captured["json"] == {
        "type": "invoice",
        "description": "Invoice for 50 x Nitrile Examination Gloves",
        "customer": {"name": "City Hospital"},
        "line_items": [
            {
                "name": "Nitrile Examination Gloves",
                "amount": 47550,
                "currency": "INR",
                "quantity": 50,
            }
        ],
        "currency": "INR",
        "notes": {"pin_code": "411001"},
    }
    assert captured["auth"] == ("rzp_test_key", "rzp_test_secret")
    assert invoice.id == "inv_ABC123"
    assert invoice.short_url == "https://rzp.io/i/invABC123"
    assert invoice.status == "issued"


# --- verify_webhook_signature -----------------------------------------------
# HMAC-SHA256 test vectors per Razorpay's documented webhook-signature scheme.


def test_verify_webhook_signature_valid():
    import hashlib
    import hmac

    secret = "webhook_secret_123"
    body = b'{"event":"payment_link.paid"}'
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, signature, secret) is True


def test_verify_webhook_signature_invalid():
    body = b'{"event":"payment_link.paid"}'

    assert verify_webhook_signature(body, "not-the-real-signature", "webhook_secret_123") is False


def test_verify_webhook_signature_wrong_secret():
    import hashlib
    import hmac

    body = b'{"event":"payment_link.paid"}'
    signature = hmac.new(b"correct_secret", body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, signature, "wrong_secret") is False


@pytest.mark.parametrize("secret,signature", [("", "somesig"), ("secret", "")])
def test_verify_webhook_signature_missing_inputs_rejected(secret, signature):
    assert verify_webhook_signature(b"{}", signature, secret) is False
