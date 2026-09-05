"""Wires the node functions into a LangGraph `StateGraph`.

Linear flow: guard_input -> extract_intent -> check_inventory -> negotiate ->
await_payment -> END, with short-circuits to END whenever guard_input lands
on Declined, or check_inventory lands on Out of stock *or* still has no
item name at all (still gathering info — asked for the product and
stopped, rather than negotiating a price for nothing), or negotiate lands
on Declined.

`guard_input` runs first and never touches the LLM: a jailbreak/prompt-
injection attempt in the buyer's own message is caught by Python before
extract_intent ever sees it, so a compromised prompt can't talk its way
into a payment link.

`await_payment` is a deliberate stopping point: it only creates the payment
link, it doesn't (and can't) know the deal is paid yet. `issue_invoice` and
`dispatch` are called directly by the Razorpay webhook handler once a real
`payment_link.paid` event confirms payment — they're plain functions in
`nodes.py`, not wired into this graph, so they aren't reachable from a
message that hasn't been paid for.
"""

from functools import lru_cache, partial

from langgraph.graph import END, StateGraph

from app.agent import nodes
from app.agent.state import DealState, DealStatus
from app.observability.tracing import traced_node
from app.services.inventory import InventoryService, get_inventory_service
from app.services.llm import LLMClient
from app.services.razorpay_client import RazorpayClient, get_razorpay_client


def _after_guard_input(state: DealState) -> str:
    return END if state.status == DealStatus.DECLINED else "extract_intent"


def _after_check_inventory(state: DealState) -> str:
    # OUT_OF_STOCK: a real, known item with insufficient stock.
    # EXTRACTING_INTENT: the buyer hasn't named an item yet at all — asked
    # for it and stopped, rather than negotiating a price for `None`.
    if state.status in (DealStatus.OUT_OF_STOCK, DealStatus.EXTRACTING_INTENT):
        return END
    return "negotiate"


def _after_negotiate(state: DealState) -> str:
    return "await_payment" if state.status != DealStatus.DECLINED else END


def build_graph(
    inventory: InventoryService | None = None,
    llm: LLMClient | None = None,
    razorpay: RazorpayClient | None = None,
):
    """Build (but don't compile-and-cache) the deal graph.

    Dependencies are injected so tests can pass fakes; production code can
    call this with no arguments to get the real inventory service, a fresh
    Groq-backed LLM client, and a real Razorpay client.
    """
    inventory = inventory or get_inventory_service()
    llm = llm or LLMClient()
    razorpay = razorpay or get_razorpay_client()

    builder = StateGraph(DealState)

    builder.add_node("guard_input", traced_node("guard_input")(nodes.guard_input))
    builder.add_node(
        "extract_intent", traced_node("extract_intent")(partial(nodes.extract_intent, llm=llm))
    )
    builder.add_node(
        "check_inventory",
        traced_node("check_inventory")(partial(nodes.check_inventory, inventory=inventory)),
    )
    builder.add_node(
        "negotiate",
        traced_node("negotiate")(partial(nodes.negotiate, inventory=inventory, llm=llm)),
    )
    builder.add_node(
        "await_payment",
        traced_node("await_payment")(partial(nodes.await_payment, razorpay=razorpay)),
    )

    builder.set_entry_point("guard_input")
    builder.add_conditional_edges("guard_input", _after_guard_input, ["extract_intent", END])
    builder.add_edge("extract_intent", "check_inventory")
    builder.add_conditional_edges(
        "check_inventory", _after_check_inventory, ["negotiate", END]
    )
    builder.add_conditional_edges("negotiate", _after_negotiate, ["await_payment", END])
    builder.add_edge("await_payment", END)

    return builder.compile()


@lru_cache
def get_compiled_graph():
    """The real, Groq/InventoryService-backed graph, built once and cached."""
    return build_graph()
