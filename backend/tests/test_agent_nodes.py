from app.agent import nodes
from app.agent.state import DealState, DealStatus, ExtractedIntent
from app.services.inventory import InventoryService


class FakeLLM:
    """Mocked LLM client — never hits the network."""

    def __init__(self, structured: ExtractedIntent | None = None, text: str = ""):
        self._structured = structured
        self._text = text

    def complete_structured(self, system, user, schema):
        return self._structured

    def complete_text(self, system, user):
        return self._text


def make_inventory() -> InventoryService:
    return InventoryService()


# --- extract_intent -----------------------------------------------------


def test_extract_intent_fills_fields_from_llm():
    llm = FakeLLM(
        structured=ExtractedIntent(
            item_name="Nitrile Examination Gloves",
            qty=50,
            hospital_name="City Hospital",
            pin_code="411001",
        )
    )
    state = DealState(messages=["Need 50 nitrile gloves to Pune, best rate?"])

    updates = nodes.extract_intent(state, llm=llm)

    assert updates["item_name"] == "Nitrile Examination Gloves"
    assert updates["qty"] == 50
    assert updates["hospital_name"] == "City Hospital"
    assert updates["pin_code"] == "411001"


def test_extract_intent_keeps_existing_fields_when_not_mentioned():
    llm = FakeLLM(structured=ExtractedIntent(item_name="Gloves", qty=None))
    state = DealState(messages=["what about gloves"], qty=50, hospital_name="City Hospital")

    updates = nodes.extract_intent(state, llm=llm)

    assert "qty" not in updates
    assert "hospital_name" not in updates
    assert updates["item_name"] == "Gloves"


def test_extract_intent_no_messages_returns_no_updates():
    llm = FakeLLM(structured=ExtractedIntent())
    state = DealState()

    assert nodes.extract_intent(state, llm=llm) == {}


# --- check_inventory ------------------------------------------------------


def test_check_inventory_in_stock():
    inventory = make_inventory()
    state = DealState(item_name="Nitrile Examination Gloves (Box of 100)", qty=50)

    updates = nodes.check_inventory(state, inventory=inventory)

    assert updates["status"] == DealStatus.CHECKING_INVENTORY
    assert updates["available_qty"] >= 50


def test_check_inventory_out_of_stock_short_circuits():
    inventory = make_inventory()
    state = DealState(item_name="Skin Stapler (Disposable)", qty=500)

    updates = nodes.check_inventory(state, inventory=inventory)

    assert updates["status"] == DealStatus.OUT_OF_STOCK
    assert "95" in updates["reply"] or str(updates["available_qty"]) in updates["reply"]
    assert "500" in updates["reply"]


def test_check_inventory_unknown_item_never_invents_stock():
    inventory = make_inventory()
    state = DealState(item_name="flux capacitor", qty=10)

    updates = nodes.check_inventory(state, inventory=inventory)

    assert updates["status"] == DealStatus.OUT_OF_STOCK
    assert updates["available_qty"] == 0


# --- negotiate --------------------------------------------------------


def test_negotiate_computes_price_python_side_and_phrases_via_llm():
    inventory = make_inventory()
    llm = FakeLLM(text="We can offer 50 units at a great rate. We will dispatch via our logistics partner post-payment.")
    state = DealState(item_name="Nitrile Examination Gloves (Box of 100)", qty=50)

    updates = nodes.negotiate(state, inventory=inventory, llm=llm)

    item = inventory.find("Nitrile Examination Gloves (Box of 100)")
    assert updates["unit_price"] <= item.base_price
    assert updates["unit_price"] >= round(item.base_price * 0.90, 2)
    assert updates["status"] == DealStatus.NEGOTIATING
    assert updates["guardrail_violations"] == []


def test_negotiate_guardrail_violation_is_caught_and_replaced():
    inventory = make_inventory()
    llm = FakeLLM(text="Don't worry, we guarantee it will be delivered in 10 minutes!")
    state = DealState(item_name="Nitrile Examination Gloves (Box of 100)", qty=50)

    updates = nodes.negotiate(state, inventory=inventory, llm=llm)

    assert "guarantee" not in updates["reply"].lower()
    assert "delivered in 10 minutes" not in updates["reply"].lower()
    assert len(updates["guardrail_violations"]) > 0


# --- stub nodes ---------------------------------------------------------


def test_await_payment_stub_transitions_status():
    state = DealState(status=DealStatus.NEGOTIATING)
    updates = nodes.await_payment(state)
    assert updates["status"] == DealStatus.AWAITING_PAYMENT


def test_issue_invoice_stub_transitions_status():
    state = DealState(status=DealStatus.AWAITING_PAYMENT)
    updates = nodes.issue_invoice(state)
    assert updates["status"] == DealStatus.ISSUING_INVOICE


def test_dispatch_stub_transitions_status():
    state = DealState(status=DealStatus.ISSUING_INVOICE)
    updates = nodes.dispatch(state)
    assert updates["status"] == DealStatus.DISPATCHED
