"""Wires the node functions into a LangGraph `StateGraph`.

Flow: guard_input -> interpret_reply -> [extract_intent -> check_inventory ->
negotiate] -> END, with `interpret_reply` able to skip straight to
`await_payment` instead of re-running extraction.

`guard_input` runs first and never touches the LLM: a jailbreak/prompt-
injection attempt in the buyer's own message is caught by Python before
extract_intent ever sees it, so a compromised prompt can't talk its way
into a payment link. Declined here ends the turn immediately.

`interpret_reply` is the *only* path to `await_payment`: an explicit
affirmative reply while the deal is `NEGOTIATING` (a price was just
proposed) is the one and only thing that creates a real Razorpay payment
link. Item + quantity + price alone are never enough — negotiate always
stops and asks "shall I send the payment link?" instead of proceeding on
its own, however complete the order looks. An explicit decline ("no",
"not now") also ends the turn right there (`handled`) with a reply
asking what to change, instead of falling through to negotiate again
and re-quoting the exact same offer verbatim.

Anything else re-enters extract_intent -> check_inventory -> negotiate, so
a clarifying answer ("10ml"), a correction ("actually make it 20"), or a
fresh lead all keep negotiating rather than being force-fit into a
confirmation. extract_intent also classifies the message as on/off topic;
a message unrelated to ordering supplies at all (`off_topic`) ends the
turn right there with a graceful redirect instead of forcing item/qty
extraction on it. check_inventory short-circuits straight to END whenever
it still needs more from the buyer (no item, no quantity, an ambiguous
item name) or the item's out of stock, instead of reaching negotiate with
nothing real to price.

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
    return END if state.status == DealStatus.DECLINED else "interpret_reply"


def _after_interpret_reply(state: DealState) -> str:
    if state.just_confirmed:
        return "await_payment"
    if state.handled:
        return END
    return "extract_intent"


def _after_extract_intent(state: DealState) -> str:
    return END if state.off_topic else "check_inventory"


def _after_check_inventory(state: DealState) -> str:
    # OUT_OF_STOCK: a real, known item with insufficient stock.
    # EXTRACTING_INTENT: still missing something (item, qty, or which
    # variant of an ambiguous item) — asked for it and stopped, rather
    # than negotiating a price for nothing.
    if state.status in (DealStatus.OUT_OF_STOCK, DealStatus.EXTRACTING_INTENT):
        return END
    return "negotiate"


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
        "interpret_reply",
        traced_node("interpret_reply")(partial(nodes.interpret_reply, inventory=inventory, llm=llm)),
    )
    builder.add_node(
        "extract_intent", traced_node("extract_intent")(partial(nodes.extract_intent, llm=llm))
    )
    builder.add_node(
        "check_inventory",
        traced_node("check_inventory")(partial(nodes.check_inventory, inventory=inventory, llm=llm)),
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
    builder.add_conditional_edges("guard_input", _after_guard_input, ["interpret_reply", END])
    builder.add_conditional_edges("interpret_reply", _after_interpret_reply, ["await_payment", "extract_intent", END])
    builder.add_conditional_edges("extract_intent", _after_extract_intent, ["check_inventory", END])
    builder.add_conditional_edges("check_inventory", _after_check_inventory, ["negotiate", END])
    builder.add_edge("negotiate", END)
    builder.add_edge("await_payment", END)

    return builder.compile()


@lru_cache
def get_compiled_graph():
    """The real, Groq/InventoryService-backed graph, built once and cached."""
    return build_graph()
