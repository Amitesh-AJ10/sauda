"""One function per LangGraph node.

Every node is a plain function of `(state, ...deps)` returning a dict of
state updates — no framework decorators, no hidden globals — so they can be
unit-tested directly and later wrapped in tracing (Task 07) without a
rewrite.
"""

import re

import httpx

from app.agent.catalog import pack_size
from app.agent.guardrails import check_prompt_injection, check_text_guardrails, clamp_price, compute_unit_price
from app.agent.prompts import EXTRACTION_INSTRUCTIONS, NEGOTIATION_INSTRUCTIONS, SYSTEM_PROMPT
from app.agent.state import DealState, DealStatus, ExtractedIntent
from app.observability.tracing import record_guardrail_result, traced_guardrail
from app.services.inventory import InventoryService
from app.services.llm import LLMClient
from app.services.razorpay_client import RazorpayClient

# Deterministic confirmation detector — only an explicit affirmative reply
# while a price is on the table is ever allowed to trigger a real Razorpay
# payment link. See `interpret_reply` below.
_CONFIRMATION_PATTERN = re.compile(
    r"\b(yes|yeah|yep|yup|sure|ok|okay|confirm(ed)?|go\s*ahead|sounds?\s*good|"
    r"please\s*send|send\s*it|that\s*works|proceed|book\s*it|place\s*the\s*order|"
    r"do\s*it|alright|good\s*to\s*go|let'?s\s*do\s*it)\b",
    re.IGNORECASE,
)


def is_confirmation(text: str) -> bool:
    return bool(_CONFIRMATION_PATTERN.search(text))


def interpret_reply(state: DealState) -> dict:
    """Deterministic gate between a proposed price and a real payment link.

    Only an explicit affirmative reply while the deal is sitting at
    `NEGOTIATING` (a price has just been proposed) sets `just_confirmed`,
    which is the *only* way the graph ever reaches `await_payment` — no
    combination of item+qty+price alone triggers it. Anything else (a
    question, a counter-offer, a correction) routes back through
    `extract_intent` to keep negotiating.
    """
    if state.status == DealStatus.NEGOTIATING and state.messages and is_confirmation(state.messages[-1]):
        return {"just_confirmed": True}
    return {"just_confirmed": False}


def guard_input(state: DealState) -> dict:
    """Deterministic pre-LLM check: block prompt-injection/jailbreak attempts
    before they ever reach the LLM, inventory, or pricing logic.

    Unlike `negotiate`'s guardrail (which catches the LLM's own unsafe
    phrasing and rewrites it, letting the deal continue), a hit here means
    the *buyer* tried to override Sauda's role — the whole graph stops
    here, Declined, with zero LLM calls made.
    """
    if not state.messages:
        return {}

    with traced_guardrail("no_prompt_injection") as span:
        violations = check_prompt_injection(state.messages[-1])
        record_guardrail_result(span, passed=not violations, detail=", ".join(violations))

    if not violations:
        return {}

    return {
        "status": DealStatus.DECLINED,
        "reply": "I can only help with product quotes and orders for this account "
        "— I can't change my instructions or role.",
        "guardrail_violations": [*state.guardrail_violations, *violations],
    }


def extract_intent(state: DealState, llm: LLMClient) -> dict:
    """LLM call → structured output, validated against `ExtractedIntent`.

    Only ever fills in fields the buyer actually mentioned; existing state
    values are kept if this message doesn't repeat them.

    Passes the *whole* conversation plus what's already on file, not just
    the latest message in isolation — a reply like "need 10" or "the 10ml
    one" has no item/qty of its own; it only means anything against the
    context of what was already asked. Extracting the last message alone
    silently lost these every time.
    """
    if not state.messages:
        return {}

    last_message = state.messages[-1]
    conversation = "\n".join(f"- {message}" for message in state.messages)
    extracted = llm.complete_structured(
        SYSTEM_PROMPT,
        EXTRACTION_INSTRUCTIONS.format(
            message=last_message,
            conversation=conversation,
            item_name=state.item_name or "not yet known",
            qty=state.qty or "not yet known",
            hospital_name=state.hospital_name or "not yet known",
            pin_code=state.pin_code or "not yet known",
        ),
        ExtractedIntent,
    )

    updates: dict = {}
    if extracted.item_name:
        updates["item_name"] = extracted.item_name
    # A real order quantity is always positive — 0 (which the LLM sometimes
    # returns instead of leaving qty blank when none was mentioned) is
    # treated the same as "not provided", never as a literal zero-unit order.
    if extracted.qty is not None and extracted.qty > 0:
        updates["qty"] = extracted.qty
    if extracted.hospital_name:
        updates["hospital_name"] = extracted.hospital_name
    if extracted.pin_code:
        updates["pin_code"] = extracted.pin_code
    return updates


def check_inventory(state: DealState, inventory: InventoryService) -> dict:
    """Deterministic stock lookup. Never lets the LLM near this decision.

    A message that hasn't named a product yet (a bare "hi", or a question
    with no item in it) is a *missing-info* case, not an out-of-stock one —
    conflating the two used to show the merchant a scary "Out of stock"
    badge and reply "Sorry, we don't currently stock 'None'" for a plain
    greeting. This asks for the item instead of guessing or declining.

    Likewise, a message that names an item but never a quantity (e.g. "do
    you have skin staplers?") must ask for the quantity here rather than
    reaching `negotiate`/`await_payment` with no real number — those nodes
    used to silently treat a missing qty as "the buyer's asking about the
    full stock," which could create a real ₹0 Razorpay payment link for
    "0 x <item>" once `state.qty` (0/None) reached `await_payment`.

    And a genuinely ambiguous item name (e.g. "disposable syringe", which
    matches both the 5ml and 10ml SKU) must ask which one rather than
    silently quoting whichever the lookup happened to match first.
    """
    if not state.item_name:
        return {
            "status": DealStatus.EXTRACTING_INTENT,
            "reply": "Hi! What product are you looking for, and how many units do you need?",
        }

    if not state.qty:
        return {
            "item_name": state.item_name,
            "status": DealStatus.EXTRACTING_INTENT,
            "reply": f"Sure — how many units of {state.item_name} do you need?",
        }

    requested_qty = state.qty
    item, ambiguous_names = inventory.resolve(state.item_name)

    if item is None and ambiguous_names:
        options = " or ".join(ambiguous_names)
        return {
            "status": DealStatus.EXTRACTING_INTENT,
            "reply": f"We carry a few options for '{state.item_name}': {options}. Which one would you like?",
        }

    available_qty = item.stock_qty if item else 0

    if item is None:
        return {
            "available_qty": 0,
            "status": DealStatus.OUT_OF_STOCK,
            "reply": f"Sorry, we don't currently stock '{state.item_name}'.",
        }

    if available_qty < requested_qty:
        return {
            "item_name": item.item_name,
            "available_qty": available_qty,
            "status": DealStatus.OUT_OF_STOCK,
            "reply": (
                f"Sorry, we only have {available_qty} units of {item.item_name} in stock "
                f"right now — short of the {requested_qty} you need. "
                f"Would you like to proceed with {available_qty} instead?"
            ),
        }

    return {
        "item_name": item.item_name,
        "available_qty": available_qty,
        "status": DealStatus.CHECKING_INVENTORY,
    }


def negotiate(state: DealState, inventory: InventoryService, llm: LLMClient) -> dict:
    """Python computes the approved price; the LLM only phrases the message.

    Never routes to `await_payment` on its own — see `interpret_reply`.
    This node's job ends at proposing a price and asking whether to send
    the payment link; only an explicit "yes" on the *next* turn can create
    one.
    """
    item, _ = inventory.resolve(state.item_name) if state.item_name else (None, [])
    if item is None:
        return {"status": DealStatus.DECLINED, "reply": "Sorry, that item is no longer available."}

    # check_inventory guarantees qty > 0 before this node ever runs; the
    # full-stock fallback only matters for a direct unit-test call. Either
    # way, persist the resolved qty below — await_payment must charge for
    # the same quantity that was just quoted, never re-derive its own.
    qty = state.qty or item.stock_qty
    raw_price = compute_unit_price(item.base_price, qty)
    with traced_guardrail("price_bounds") as span:
        unit_price = clamp_price(raw_price, item.base_price)
        clamped = unit_price != raw_price
        record_guardrail_result(
            span, passed=not clamped, detail=f"proposed {raw_price} -> clamped to {unit_price}"
        )

    prompt = NEGOTIATION_INSTRUCTIONS.format(
        item_name=item.item_name,
        available_qty=item.stock_qty,
        qty=qty,
        unit_price=unit_price,
        hospital_name=state.hospital_name or "not provided yet",
        pin_code=state.pin_code or "not provided yet",
    )
    reply = llm.complete_text(SYSTEM_PROMPT, prompt)

    with traced_guardrail("no_sla_promise") as span:
        violations = check_text_guardrails(reply)
        record_guardrail_result(span, passed=not violations, detail=", ".join(violations))
        if violations:
            reply = _safe_negotiation_reply(item.item_name, qty, unit_price, state)

    reply = f"{reply} {_packaging_note(item.item_name, qty)}".strip()
    reply = f"{reply} Shall I go ahead and send the payment link?"

    return {
        "qty": qty,
        "unit_price": unit_price,
        "status": DealStatus.NEGOTIATING,
        "reply": reply,
        "guardrail_violations": [*state.guardrail_violations, *violations],
    }


def _packaging_note(item_name: str, qty: int) -> str:
    """Deterministic packaging clarity for a '(Box of N)' item — Python states
    what a bare quantity actually means, rather than leaving it for the
    buyer to assume units when the catalog sells boxes (or vice versa)."""
    pack = pack_size(item_name)
    if not pack:
        return ""
    box_word = "box" if qty == 1 else "boxes"
    return f"Note: this ships in boxes of {pack} units, so {qty} = {qty} {box_word} ({qty * pack} units total)."


def _safe_negotiation_reply(item_name: str, qty: int, unit_price: float, state: DealState) -> str:
    """Deterministic fallback used whenever the LLM's phrasing trips a guardrail."""
    missing = []
    if not state.hospital_name:
        missing.append("your hospital name")
    if not state.pin_code:
        missing.append("your delivery PIN code")
    ask = f" Could you also share {' and '.join(missing)} to verify logistics?" if missing else ""
    return (
        f"We can offer {qty} units of {item_name} at INR {unit_price} per unit."
        f"{ask} We will dispatch via our logistics partner post-payment."
    )


def await_payment(state: DealState, razorpay: RazorpayClient) -> dict:
    """Deterministically create a Razorpay payment link for the agreed terms.

    `qty * unit_price` is computed here in Python (never by the LLM) and
    converted to paise, per PRD guardrail F/G3.

    Last-line defense: never call Razorpay for a ₹0 link. `check_inventory`
    already refuses to reach `negotiate` without a real qty, but this node
    doesn't re-trust that — a zero/missing qty or price here declines
    instead of creating a real, live ₹0 payment link.
    """
    qty = state.qty or 0
    unit_price = state.unit_price or 0.0

    if qty <= 0 or unit_price <= 0:
        return {
            "status": DealStatus.DECLINED,
            "reply": "Sorry, we couldn't confirm a quantity and price for this order — could you resend it?",
        }

    amount_paise = round(qty * unit_price * 100)

    link = razorpay.create_payment_link(
        amount_paise=amount_paise,
        description=f"{qty} x {state.item_name}",
        notes={
            "item_name": state.item_name or "",
            "hospital_name": state.hospital_name or "",
            "pin_code": state.pin_code or "",
        },
    )

    return {
        "status": DealStatus.AWAITING_PAYMENT,
        "payment_link_id": link.id,
        "payment_link_url": link.short_url,
        "reply": f"Please complete payment to confirm your order: {link.short_url}",
    }


def issue_invoice(state: DealState, razorpay: RazorpayClient) -> dict:
    """Once payment is confirmed, autonomously generate the GST invoice.

    Called directly by the Razorpay webhook handler once `status == Paid`
    (not part of the WhatsApp-triggered graph — see await_payment). A
    failed invoice call never silently marks the deal `Dispatched`; the
    deal is left in `INVOICE_FAILED` for retry/inspection instead.
    """
    try:
        invoice = razorpay.create_invoice(state)
    except httpx.HTTPError:
        return {"status": DealStatus.INVOICE_FAILED}

    return {
        "status": DealStatus.DISPATCHED,
        "invoice_url": invoice.short_url,
        "reply": (
            f"Payment received! Here is your GST invoice: {invoice.short_url}. "
            "Your order has been dispatched via our logistics partner."
        ),
    }


def dispatch(state: DealState) -> dict:
    """Stub: real logistics dispatch trigger lands in a later task."""
    return {
        "status": DealStatus.DISPATCHED,
        "reply": "Your order has been dispatched via our logistics partner.",
    }
