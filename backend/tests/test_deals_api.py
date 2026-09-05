from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations
from app.data.hospitals import list_hospitals
from app.main import app
from app.services.razorpay_client import get_razorpay_client
from app.services.whatsapp import get_whatsapp_service

client = TestClient(app)


def test_lists_all_hardcoded_hospitals_even_with_no_conversations():
    app.dependency_overrides[get_conversations] = lambda: {}

    response = client.get("/api/v1/deals")

    assert response.status_code == 200
    deals = response.json()
    assert {deal["id"] for deal in deals} == {hospital.id for hospital in list_hospitals()}
    assert all(deal["status"] is None for deal in deals)
    assert all(deal["messages"] == [] for deal in deals)

    app.dependency_overrides.clear()


def test_lists_deals_from_conversation_store():
    hospital = list_hospitals()[0]
    conversations = {
        hospital.id: DealState(
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
    assert deals[hospital.id]["status"] == "negotiating"
    assert deals[hospital.id]["hospital_name"] == "City Care"
    assert deals["919999999999"]["status"] == "paid"
    assert deals["919999999999"]["payment_link_url"] == "https://rzp.io/i/fake"
    assert deals["919999999999"]["invoice_url"] == "https://rzp.io/invoice/fake"

    app.dependency_overrides.clear()


def test_awaiting_payment_deal_is_finalized_when_razorpay_reports_paid():
    hospital = list_hospitals()[0]
    conversations = {
        hospital.id: DealState(
            hospital_name=hospital.name,
            item_name="Nitrile Gloves",
            qty=50,
            unit_price=100.0,
            status=DealStatus.AWAITING_PAYMENT,
            payment_link_id="plink_fake123",
            payment_link_url="https://rzp.io/i/fake123",
        )
    }

    class FakeRazorpay:
        def get_payment_link_status(self, payment_link_id: str) -> str:
            return "paid"

        def create_invoice(self, deal):
            from app.services.razorpay_client import Invoice

            return Invoice(id="inv_fake", short_url="https://rzp.io/i/invfake", status="issued")

    class FakeWhatsApp:
        def send_message(self, to: str, text: str) -> dict:
            return {"messages": [{"id": "wamid.fake"}]}

    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_razorpay_client] = lambda: FakeRazorpay()
    app.dependency_overrides[get_whatsapp_service] = lambda: FakeWhatsApp()

    response = client.get("/api/v1/deals")

    assert response.status_code == 200
    deals = {deal["id"]: deal for deal in response.json()}
    assert deals[hospital.id]["status"] == "dispatched"
    assert deals[hospital.id]["invoice_url"] == "https://rzp.io/i/invfake"
    assert conversations[hospital.id].status == DealStatus.DISPATCHED

    app.dependency_overrides.clear()


def test_awaiting_payment_deal_stays_awaiting_when_razorpay_reports_unpaid():
    hospital = list_hospitals()[0]
    conversations = {
        hospital.id: DealState(
            hospital_name=hospital.name,
            item_name="Nitrile Gloves",
            qty=50,
            unit_price=100.0,
            status=DealStatus.AWAITING_PAYMENT,
            payment_link_id="plink_fake123",
            payment_link_url="https://rzp.io/i/fake123",
        )
    }

    class FakeRazorpay:
        def get_payment_link_status(self, payment_link_id: str) -> str:
            return "created"

    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_razorpay_client] = lambda: FakeRazorpay()

    response = client.get("/api/v1/deals")

    assert response.status_code == 200
    deals = {deal["id"]: deal for deal in response.json()}
    assert deals[hospital.id]["status"] == "awaiting_payment"

    app.dependency_overrides.clear()
