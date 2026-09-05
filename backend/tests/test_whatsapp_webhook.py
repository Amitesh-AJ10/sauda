import pytest
from fastapi.testclient import TestClient

from app.agent.state import DealState, DealStatus
from app.api.whatsapp import get_conversations, get_graph
from app.main import app
from app.services.whatsapp import get_whatsapp_service

client = TestClient(app)


class FakeGraph:
    """Records every state it's invoked with; returns a canned result."""

    def __init__(self, reply: str = "Thanks, here's our offer.", status: DealStatus = DealStatus.NEGOTIATING):
        self.calls: list[DealState] = []
        self._reply = reply
        self._status = status

    def invoke(self, state: DealState) -> dict:
        self.calls.append(state.model_copy(deep=True))
        return {**state.model_dump(), "reply": self._reply, "status": self._status}


class FakeWhatsAppService:
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send_message(self, to: str, text: str) -> dict:
        self.sent.append((to, text))
        return {"messages": [{"id": "wamid.fake"}]}


def inbound_payload(sender: str, text: str) -> dict:
    return {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": sender, "type": "text", "text": {"body": text}}
                            ]
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# --- verification handshake ---------------------------------------------


def test_verify_webhook_correct_token_echoes_challenge(monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "secret123")

    response = client.get(
        "/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "secret123", "hub.challenge": "12345"},
    )

    assert response.status_code == 200
    assert response.text == "12345"


def test_verify_webhook_wrong_token_is_rejected(monkeypatch):
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "secret123")

    response = client.get(
        "/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": "wrong-token", "hub.challenge": "12345"},
    )

    assert response.status_code == 403


# --- inbound message handling --------------------------------------------


def test_inbound_message_drives_graph_and_sends_exactly_one_reply():
    fake_graph = FakeGraph(reply="Here's our best rate for 50 gloves.")
    fake_whatsapp = FakeWhatsAppService()
    app.dependency_overrides[get_graph] = lambda: fake_graph
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp
    app.dependency_overrides[get_conversations] = lambda: {}

    response = client.post("/webhooks/whatsapp", json=inbound_payload("911234567890", "Need 50 gloves, best rate?"))

    assert response.status_code == 200
    assert len(fake_graph.calls) == 1
    assert fake_graph.calls[0].messages == ["Need 50 gloves, best rate?"]
    assert fake_whatsapp.sent == [("911234567890", "Here's our best rate for 50 gloves.")]


def test_non_message_payload_is_ignored():
    fake_graph = FakeGraph()
    fake_whatsapp = FakeWhatsAppService()
    app.dependency_overrides[get_graph] = lambda: fake_graph
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp
    app.dependency_overrides[get_conversations] = lambda: {}

    status_payload = {"entry": [{"changes": [{"value": {"statuses": [{"status": "delivered"}]}}]}]}
    response = client.post("/webhooks/whatsapp", json=status_payload)

    assert response.status_code == 200
    assert fake_graph.calls == []
    assert fake_whatsapp.sent == []


# --- state resumption -----------------------------------------------------


def test_unknown_sender_starts_fresh_state_known_sender_resumes():
    fake_graph = FakeGraph(reply="ok")
    fake_whatsapp = FakeWhatsAppService()
    conversations: dict = {}
    app.dependency_overrides[get_graph] = lambda: fake_graph
    app.dependency_overrides[get_whatsapp_service] = lambda: fake_whatsapp
    app.dependency_overrides[get_conversations] = lambda: conversations

    sender = "919999999999"
    client.post("/webhooks/whatsapp", json=inbound_payload(sender, "Need 20 masks"))
    client.post("/webhooks/whatsapp", json=inbound_payload(sender, "Hospital is City Care, PIN 411001"))

    assert len(fake_graph.calls) == 2
    # first call: fresh state, only the first message
    assert fake_graph.calls[0].messages == ["Need 20 masks"]
    # second call: resumed state carries the first message forward too
    assert fake_graph.calls[1].messages == ["Need 20 masks", "Hospital is City Care, PIN 411001"]
    assert sender in conversations
