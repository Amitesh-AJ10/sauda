from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations, get_graph
from app.data.hospitals import list_hospitals
from app.main import app
from app.services.razorpay_client import Invoice, get_razorpay_client
from app.services.whatsapp import get_whatsapp_service

client = TestClient(app)


class FakeGraph:
    """Mirrors the real graph's shape: negotiates straight to AWAITING_PAYMENT."""

    def invoke(self, state: DealState) -> dict:
        return {
            **state.model_dump(),
            "item_name": "Nitrile Examination Gloves",
            "qty": 100,
            "unit_price": 179.0,
            "available_qty": 500,
            "status": DealStatus.AWAITING_PAYMENT,
            "payment_link_id": "plink_CHAT123",
            "payment_link_url": "https://rzp.io/i/CHAT123",
            "reply": "Please complete payment: https://rzp.io/i/CHAT123",
        }


def test_get_hospitals_lists_the_fixed_directory():
    response = client.get("/api/v1/hospitals")

    assert response.status_code == 200
    ids = {hospital["id"] for hospital in response.json()}
    assert ids == {hospital.id for hospital in list_hospitals()}


def test_unknown_hospital_404s():
    response = client.post("/api/v1/chat/not-a-real-hospital/messages", json={"text": "hi"})

    assert response.status_code == 404


def test_sending_a_message_runs_the_real_graph_and_stores_the_deal():
    hospital = list_hospitals()[0]
    conversations: dict = {}
    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_graph] = lambda: FakeGraph()

    response = client.post(f"/api/v1/chat/{hospital.id}/messages", json={"text": "Need 100 boxes of gloves"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "awaiting_payment"
    assert body["payment_link_url"] == "https://rzp.io/i/CHAT123"
    assert "🔗 Razorpay payment link generated" in body["audit_trail"]
    assert conversations[hospital.id].hospital_name == hospital.name

    app.dependency_overrides.clear()


def test_seeds_hospital_name_and_pin_from_directory_on_first_message():
    hospital = list_hospitals()[1]
    conversations: dict = {}
    captured_state: dict = {}

    class RecordingGraph:
        def invoke(self, state: DealState) -> dict:
            captured_state["hospital_name"] = state.hospital_name
            captured_state["pin_code"] = state.pin_code
            return {**state.model_dump(), "status": DealStatus.EXTRACTING_INTENT}

    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_graph] = lambda: RecordingGraph()

    client.post(f"/api/v1/chat/{hospital.id}/messages", json={"text": "hello"})

    assert captured_state["hospital_name"] == hospital.name
    assert captured_state["pin_code"] == hospital.pin_code

    app.dependency_overrides.clear()


# --- locked-state messages (awaiting payment or beyond) --------------------


class ExplodingGraph:
    """Any call means a locked-state message wrongly restarted negotiation."""

    def invoke(self, state: DealState) -> dict:
        raise AssertionError("the graph should never run for a message while a deal is locked")


def test_awaiting_payment_message_checks_razorpay_for_real_instead_of_restarting():
    hospital = list_hospitals()[0]
    conversations = {
        hospital.id: DealState(
            hospital_name=hospital.name,
            item_name="Alcohol Swabs (Box of 100)",
            qty=400,
            unit_price=56.4,
            status=DealStatus.AWAITING_PAYMENT,
            payment_link_id="plink_fake123",
            payment_link_url="https://rzp.io/i/fake123",
        )
    }

    class FakeRazorpay:
        def get_payment_link_status(self, payment_link_id: str) -> str:
            return "paid"

        def create_invoice(self, deal: DealState) -> Invoice:
            return Invoice(id="inv_fake", short_url="https://rzp.io/i/invfake", status="issued")

    class FakeWhatsApp:
        def send_message(self, to: str, text: str) -> dict:
            return {"messages": [{"id": "wamid.fake"}]}

    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_graph] = lambda: ExplodingGraph()
    app.dependency_overrides[get_razorpay_client] = lambda: FakeRazorpay()
    app.dependency_overrides[get_whatsapp_service] = lambda: FakeWhatsApp()

    response = client.post(f"/api/v1/chat/{hospital.id}/messages", json={"text": "payment done"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispatched"
    assert body["invoice_url"] == "https://rzp.io/i/invfake"

    app.dependency_overrides.clear()


def test_awaiting_payment_message_stays_awaiting_when_not_actually_paid():
    hospital = list_hospitals()[0]
    conversations = {
        hospital.id: DealState(
            hospital_name=hospital.name,
            item_name="Alcohol Swabs (Box of 100)",
            qty=400,
            unit_price=56.4,
            status=DealStatus.AWAITING_PAYMENT,
            payment_link_id="plink_fake123",
            payment_link_url="https://rzp.io/i/fake123",
        )
    }

    class FakeRazorpay:
        def get_payment_link_status(self, payment_link_id: str) -> str:
            return "created"

    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_graph] = lambda: ExplodingGraph()
    app.dependency_overrides[get_razorpay_client] = lambda: FakeRazorpay()

    response = client.post(f"/api/v1/chat/{hospital.id}/messages", json={"text": "payment done"})

    assert response.status_code == 200
    body = response.json()
    # Regression: this used to fall through to the full graph, which reset
    # status back to negotiating and re-quoted the offer from scratch.
    assert body["status"] == "awaiting_payment"
    assert conversations[hospital.id].item_name == "Alcohol Swabs (Box of 100)"
    assert conversations[hospital.id].qty == 400
    assert "don't see that payment reflected" in body["reply"].lower()

    app.dependency_overrides.clear()


def test_non_payment_message_while_awaiting_payment_gets_the_link_again_unchanged():
    hospital = list_hospitals()[0]
    conversations = {
        hospital.id: DealState(
            hospital_name=hospital.name,
            item_name="Alcohol Swabs (Box of 100)",
            qty=400,
            unit_price=56.4,
            status=DealStatus.AWAITING_PAYMENT,
            payment_link_id="plink_fake123",
            payment_link_url="https://rzp.io/i/fake123",
        )
    }

    class FakeRazorpay:
        def get_payment_link_status(self, payment_link_id: str) -> str:
            return "created"

    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_graph] = lambda: ExplodingGraph()
    app.dependency_overrides[get_razorpay_client] = lambda: FakeRazorpay()

    response = client.post(f"/api/v1/chat/{hospital.id}/messages", json={"text": "is the price negotiable?"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "awaiting_payment"
    assert "https://rzp.io/i/fake123" in body["reply"]
    assert conversations[hospital.id].qty == 400

    app.dependency_overrides.clear()


def test_dispatched_message_never_touches_the_graph():
    hospital = list_hospitals()[0]
    conversations = {
        hospital.id: DealState(
            hospital_name=hospital.name,
            status=DealStatus.DISPATCHED,
            invoice_url="https://rzp.io/i/invfake",
        )
    }

    app.dependency_overrides[get_conversations] = lambda: conversations
    app.dependency_overrides[get_graph] = lambda: ExplodingGraph()

    response = client.post(f"/api/v1/chat/{hospital.id}/messages", json={"text": "thanks!"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "dispatched"
    assert "https://rzp.io/i/invfake" in body["reply"]

    app.dependency_overrides.clear()
