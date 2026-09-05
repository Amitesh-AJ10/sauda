from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations
from app.main import app

client = TestClient(app)


def test_no_deals_returns_empty_list():
    app.dependency_overrides[get_conversations] = lambda: {}

    response = client.get("/api/v1/deals")

    assert response.status_code == 200
    assert response.json() == []

    app.dependency_overrides.clear()


def test_lists_deals_from_conversation_store():
    conversations = {
        "911234567890": DealState(
            hospital_name="City Care",
            item_name="Nitrile Gloves",
            qty=50,
            status=DealStatus.NEGOTIATING,
        ),
        "919999999999": DealState(
            hospital_name="Sunrise Hospital",
            item_name="Surgical Masks",
            qty=200,
            status=DealStatus.PAID,
            payment_link_url="https://rzp.io/i/fake",
            invoice_url="https://rzp.io/invoice/fake",
        ),
    }
    app.dependency_overrides[get_conversations] = lambda: conversations

    response = client.get("/api/v1/deals")

    assert response.status_code == 200
    deals = {deal["id"]: deal for deal in response.json()}
    assert deals["911234567890"]["status"] == "negotiating"
    assert deals["911234567890"]["hospital_name"] == "City Care"
    assert deals["919999999999"]["status"] == "paid"
    assert deals["919999999999"]["payment_link_url"] == "https://rzp.io/i/fake"
    assert deals["919999999999"]["invoice_url"] == "https://rzp.io/invoice/fake"

    app.dependency_overrides.clear()
