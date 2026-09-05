from app.agent.graph import build_graph
from app.agent.state import DealState, DealStatus, ExtractedIntent
from app.services.inventory import InventoryService


class FakeLLM:
    """Mocked LLM client for full-graph runs — no real API calls."""

    def __init__(self, structured: ExtractedIntent, text: str):
        self._structured = structured
        self._text = text

    def complete_structured(self, system, user, schema):
        return self._structured

    def complete_text(self, system, user):
        return self._text


def make_inventory() -> InventoryService:
    return InventoryService()


def test_happy_path_runs_end_to_end_to_dispatched():
    llm = FakeLLM(
        structured=ExtractedIntent(
            item_name="Nitrile Examination Gloves",
            qty=50,
            hospital_name="City Hospital",
            pin_code="411001",
        ),
        text="We can offer 50 boxes at a fair rate. We will dispatch via our logistics partner post-payment.",
    )
    graph = build_graph(inventory=make_inventory(), llm=llm)

    result = graph.invoke(DealState(messages=["Need 50 nitrile gloves, best rate?"]))

    assert result["status"] == DealStatus.DISPATCHED
    assert result["unit_price"] is not None
    assert result["available_qty"] >= 50


def test_out_of_stock_short_circuits_with_apology_never_inventing_stock():
    llm = FakeLLM(
        structured=ExtractedIntent(item_name="Skin Stapler", qty=500),
        text="this should never be called",
    )
    graph = build_graph(inventory=make_inventory(), llm=llm)

    result = graph.invoke(DealState(messages=["Need 500 surgical staplers to Pune, best rate?"]))

    assert result["status"] == DealStatus.OUT_OF_STOCK
    item = make_inventory().find("Skin Stapler")
    assert str(item.stock_qty) in result["reply"]
    assert "500" in result["reply"]


def test_guardrail_violation_caught_before_reaching_buyer():
    llm = FakeLLM(
        structured=ExtractedIntent(item_name="Nitrile Examination Gloves", qty=50),
        text="We guarantee it will be delivered in 10 minutes, no questions asked!",
    )
    graph = build_graph(inventory=make_inventory(), llm=llm)

    result = graph.invoke(DealState(messages=["Need 50 gloves urgently, best rate?"]))

    assert "guarantee" not in result["reply"].lower()
    assert "delivered in 10 minutes" not in result["reply"].lower()
    assert len(result["guardrail_violations"]) > 0
    # guardrail catch doesn't block the rest of the (stubbed) pipeline
    assert result["status"] == DealStatus.DISPATCHED
