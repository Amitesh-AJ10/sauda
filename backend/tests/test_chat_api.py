from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations, get_graph
from app.data.hospitals import list_hospitals
from app.main import app

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
