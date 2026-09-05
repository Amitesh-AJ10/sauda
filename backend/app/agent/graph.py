"""Wires the node functions into a LangGraph `StateGraph`.

Linear flow: extract_intent -> check_inventory -> negotiate -> await_payment
-> issue_invoice -> dispatch -> END, with short-circuits to END whenever
check_inventory or negotiate lands on a terminal status (out of stock /
declined) instead of progressing.
"""

from functools import lru_cache, partial

from langgraph.graph import END, StateGraph

from app.agent import nodes
from app.agent.state import DealState, DealStatus
from app.services.inventory import InventoryService, get_inventory_service
from app.services.llm import LLMClient


def _after_check_inventory(state: DealState) -> str:
    return "negotiate" if state.status != DealStatus.OUT_OF_STOCK else END


def _after_negotiate(state: DealState) -> str:
    return "await_payment" if state.status != DealStatus.DECLINED else END


def build_graph(
    inventory: InventoryService | None = None,
    llm: LLMClient | None = None,
):
    """Build (but don't compile-and-cache) the deal graph.

    Dependencies are injected so tests can pass fakes; production code can
    call this with no arguments to get the real inventory service and a
    fresh Groq-backed LLM client.
    """
    inventory = inventory or get_inventory_service()
    llm = llm or LLMClient()

    builder = StateGraph(DealState)

    builder.add_node("extract_intent", partial(nodes.extract_intent, llm=llm))
    builder.add_node("check_inventory", partial(nodes.check_inventory, inventory=inventory))
    builder.add_node("negotiate", partial(nodes.negotiate, inventory=inventory, llm=llm))
    builder.add_node("await_payment", nodes.await_payment)
    builder.add_node("issue_invoice", nodes.issue_invoice)
    builder.add_node("dispatch", nodes.dispatch)

    builder.set_entry_point("extract_intent")
    builder.add_edge("extract_intent", "check_inventory")
    builder.add_conditional_edges(
        "check_inventory", _after_check_inventory, ["negotiate", END]
    )
    builder.add_conditional_edges("negotiate", _after_negotiate, ["await_payment", END])
    builder.add_edge("await_payment", "issue_invoice")
    builder.add_edge("issue_invoice", "dispatch")
    builder.add_edge("dispatch", END)

    return builder.compile()


@lru_cache
def get_compiled_graph():
    """The real, Groq/InventoryService-backed graph, built once and cached."""
    return build_graph()
