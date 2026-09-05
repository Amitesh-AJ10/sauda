"""One function per LangGraph node.

Every node is a plain function of `(state, ...deps)` returning a dict of
state updates — no framework decorators, no hidden globals — so they can be
unit-tested directly and later wrapped in tracing (Task 07) without a
rewrite.
"""

import httpx

from app.agent.guardrails import check_text_guardrails, clamp_price, compute_unit_price
from app.agent.prompts import EXTRACTION_INSTRUCTIONS, NEGOTIATION_INSTRUCTIONS, SYSTEM_PROMPT
from app.agent.state import DealState, DealStatus, ExtractedIntent
from app.services.inventory import InventoryService
from app.services.llm import LLMClient
from app.services.razorpay_client import RazorpayClient


def extract_intent(state: DealState, llm: LLMClient) -> dict:
    """LLM call → structured output, validated against `ExtractedIntent`.

    Only ever fills in fields the buyer actually mentioned; existing state
    values are kept if this message doesn't repeat them.
    """
    if not state.messages:
        return {}

    last_message = state.messages[-1]
    extracted = llm.complete_structured(
        SYSTEM_PROMPT,
        EXTRACTION_INSTRUCTIONS.format(message=last_message),
        ExtractedIntent,
    )

    updates: dict = {}
    if extracted.item_name:
        updates["item_name"] = extracted.item_name
    if extracted.qty is not None:
        updates["qty"] = extracted.qty
    if extracted.hospital_name:
        updates["hospital_name"] = extracted.hospital_name
    if extracted.pin_code:
        updates["pin_code"] = extracted.pin_code
    return updates


def check_inventory(state: DealState, inventory: InventoryService) -> dict:
    """Deterministic stock lookup. Never lets the LLM near this decision."""
    requested_qty = state.qty or 0
    item = inventory.find(state.item_name) if state.item_name else None
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
    """Python computes the approved price; the LLM only phrases the message."""
    item = inventory.find(state.item_name) if state.item_name else None
    if item is None:
        return {"status": DealStatus.DECLINED, "reply": "Sorry, that item is no longer available."}

    qty = state.qty or item.stock_qty
    unit_price = clamp_price(compute_unit_price(item.base_price, qty), item.base_price)

    prompt = NEGOTIATION_INSTRUCTIONS.format(
        item_name=item.item_name,
        available_qty=item.stock_qty,
        qty=qty,
        unit_price=unit_price,
        hospital_name=state.hospital_name or "not provided yet",
        pin_code=state.pin_code or "not provided yet",
    )
    reply = llm.complete_text(SYSTEM_PROMPT, prompt)

    violations = check_text_guardrails(reply)
    if violations:
        reply = _safe_negotiation_reply(item.item_name, qty, unit_price, state)

    return {
        "unit_price": unit_price,
        "status": DealStatus.NEGOTIATING,
        "reply": reply,
        "guardrail_violations": [*state.guardrail_violations, *violations],
    }


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
    """
    qty = state.qty or 0
    unit_price = state.unit_price or 0.0
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
