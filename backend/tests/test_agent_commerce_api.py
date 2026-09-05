import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.agent_commerce import get_orders
from app.main import app
from app.services.razorpay_client import PaymentLink, get_razorpay_client

client = TestClient(app)

API_KEY = "test-agent-key"
HEADERS = {"X-API-Key": API_KEY}

# Real inventory item names from app/data/mock_inventory.csv, used elsewhere
# in the test suite too (see tests/test_agent_nodes.py).
IN_STOCK_ITEM = "Nitrile Examination Gloves (Box of 100)"
LOW_STOCK_ITEM = "Skin Stapler (Disposable)"  # 95 units in stock


class FakeRazorpay:
    def __init__(self, link: PaymentLink | None = None):
        self._link = link or PaymentLink(id="plink_agent123", short_url="https://rzp.io/i/agent123", status="created")
        self.calls: list[tuple[int, str, dict]] = []

    def create_payment_link(self, amount_paise: int, description: str, notes: dict) -> PaymentLink:
        self.calls.append((amount_paise, description, notes))
        return self._link


def sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch):
    monkeypatch.setenv("AGENT_API_KEY", API_KEY)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


# --- auth -----------------------------------------------------------------


@pytest.mark.parametrize(
    "method, path, json_body",
    [
        ("post", "/api/v1/quote", {"item_name": IN_STOCK_ITEM, "qty": 10, "pin_code": "411001"}),
        ("post", "/api/v1/orders", {"item_name": IN_STOCK_ITEM, "qty": 10, "pin_code": "411001"}),
        ("get", "/api/v1/orders/plink_whatever", None),
    ],
)
def test_missing_api_key_rejected_with_401(method, path, json_body):
    response = client.request(method, path, json=json_body)
    assert response.status_code == 401


@pytest.mark.parametrize(
    "method, path, json_body",
    [
        ("post", "/api/v1/quote", {"item_name": IN_STOCK_ITEM, "qty": 10, "pin_code": "411001"}),
        ("post", "/api/v1/orders", {"item_name": IN_STOCK_ITEM, "qty": 10, "pin_code": "411001"}),
        ("get", "/api/v1/orders/plink_whatever", None),
    ],
)
def test_wrong_api_key_rejected_with_401(method, path, json_body):
    response = client.request(method, path, json=json_body, headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


# --- POST /api/v1/quote ----------------------------------------------------


def test_quote_in_stock_item_returns_correct_price_no_llm_call():
    response = client.post(
        "/api/v1/quote", json={"item_name": IN_STOCK_ITEM, "qty": 50, "pin_code": "411001"}, headers=HEADERS
    )

    assert response.status_code == 200
    body = response.json()
    assert body["available_qty"] >= 50
    assert body["unit_price"] > 0
    assert body["total_price"] == round(body["unit_price"] * 50, 2)
    assert body["currency"] == "INR"


def test_quote_over_stock_request_returns_available_quantity_not_an_error():
    response = client.post(
        "/api/v1/quote", json={"item_name": LOW_STOCK_ITEM, "qty": 500, "pin_code": "411001"}, headers=HEADERS
    )

    assert response.status_code == 200
    body = response.json()
    assert 0 < body["available_qty"] < 500
    # priced for what's actually available, not the over-ask
    assert body["total_price"] == round(body["unit_price"] * body["available_qty"], 2)


def test_quote_unknown_item_returns_404():
    response = client.post(
        "/api/v1/quote", json={"item_name": "flux capacitor", "qty": 10, "pin_code": "411001"}, headers=HEADERS
    )

    assert response.status_code == 404


# --- POST /api/v1/orders + GET /api/v1/orders/{id} -------------------------


def test_create_order_produces_a_real_payment_link_like_the_whatsapp_flow():
    fake_razorpay = FakeRazorpay(
        PaymentLink(id="plink_agent123", short_url="https://rzp.io/i/agent123", status="created")
    )
    app.dependency_overrides[get_razorpay_client] = lambda: fake_razorpay

    response = client.post(
        "/api/v1/orders",
        json={"item_name": IN_STOCK_ITEM, "qty": 50, "pin_code": "411001", "hospital_name": "City Hospital"},
        headers=HEADERS,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["order_id"] == "plink_agent123"
    assert body["payment_link_url"] == "https://rzp.io/i/agent123"
    assert body["status"] == DealStatus.AWAITING_PAYMENT.value
    assert len(fake_razorpay.calls) == 1
    amount_paise, description, notes = fake_razorpay.calls[0]
    assert amount_paise > 0
    assert "50" in description
    assert notes["hospital_name"] == "City Hospital"


def test_order_status_polling_reflects_state_before_and_after_payment(monkeypatch):
    orders: dict[str, DealState] = {}
    fake_razorpay = FakeRazorpay(
        PaymentLink(id="plink_agent456", short_url="https://rzp.io/i/agent456", status="created")
    )
    app.dependency_overrides[get_orders] = lambda: orders
    app.dependency_overrides[get_razorpay_client] = lambda: fake_razorpay

    create_response = client.post(
        "/api/v1/orders",
        json={"item_name": IN_STOCK_ITEM, "qty": 20, "pin_code": "411001"},
        headers=HEADERS,
    )
    order_id = create_response.json()["order_id"]

    before = client.get(f"/api/v1/orders/{order_id}", headers=HEADERS)
    assert before.status_code == 200
    assert before.json()["status"] == DealStatus.AWAITING_PAYMENT.value

    # Simulate the Razorpay webhook confirming payment for this order.
    from app.services.razorpay_client import Invoice

    class FakeRazorpayInvoice(FakeRazorpay):
        def create_invoice(self, deal: DealState) -> Invoice:
            return Invoice(id="inv_agent456", short_url="https://rzp.io/i/invagent456", status="issued")

    fake_razorpay_full = FakeRazorpayInvoice(fake_razorpay._link)
    app.dependency_overrides[get_razorpay_client] = lambda: fake_razorpay_full

    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "whsec_test")
    body = json.dumps(
        {"event": "payment_link.paid", "payload": {"payment_link": {"entity": {"id": order_id}}}}
    ).encode()
    webhook_response = client.post(
        "/webhooks/razorpay",
        content=body,
        headers={"X-Razorpay-Signature": sign(body, "whsec_test")},
    )
    assert webhook_response.status_code == 200

    after = client.get(f"/api/v1/orders/{order_id}", headers=HEADERS)
    assert after.status_code == 200
    after_body = after.json()
    assert after_body["status"] == DealStatus.DISPATCHED.value
    assert after_body["invoice_url"] == "https://rzp.io/i/invagent456"


def test_order_status_unknown_order_id_returns_404():
    response = client.get("/api/v1/orders/does-not-exist", headers=HEADERS)
    assert response.status_code == 404
