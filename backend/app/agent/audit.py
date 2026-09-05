"""Deterministic, plain-language audit trail for the merchant dashboard.

Built straight from `DealState` fields — no LLM involved, and deliberately
not the raw Phoenix/OpenTelemetry trace (that's the engineering-level
detail; PRD Task 10 keeps it out of the merchant-facing UI). Each line
names something Python actually decided, so a guardrail catch or a stock
check reads as a fact the merchant can trust, not an LLM's summary of
itself.
"""

from app.agent.state import DealState, DealStatus


def build_audit_trail(state: DealState) -> list[str]:
    if not state.messages:
        return []

    trail = [f'📩 Message received: "{state.messages[-1]}"']

    # Blocked before the LLM ever saw it — no inventory check, no price, no link.
    if state.status == DealStatus.DECLINED and state.guardrail_violations:
        trail.append("🚫 Guardrail blocked this message before it reached the AI")
        trail.append("⛔ Declined — no inventory check, no payment link generated")
        return trail

    if state.status == DealStatus.OUT_OF_STOCK:
        trail.append(f"🔍 Checked inventory for '{state.item_name}'")
        trail.append(f"❌ Out of stock — only {state.available_qty or 0} available")
        return trail

    if state.item_name:
        trail.append(f"🔍 Checked inventory for '{state.item_name}'")
    if state.available_qty is not None:
        trail.append(f"✅ Stock confirmed: {state.available_qty} units available")
    if state.unit_price is not None:
        trail.append(f"💰 Price set: ₹{state.unit_price}/unit — computed by Python, never the LLM")
    for violation in state.guardrail_violations:
        trail.append(f"🚫 Guardrail rewrote an unsafe reply (matched: {violation})")
    if state.payment_link_url:
        trail.append("🔗 Razorpay payment link generated")
    if state.status in (DealStatus.PAID, DealStatus.ISSUING_INVOICE, DealStatus.DISPATCHED):
        trail.append("✅ Payment confirmed by Razorpay")
    if state.invoice_url:
        trail.append("🧾 GST invoice generated and sent")
    if state.status == DealStatus.DISPATCHED:
        trail.append("🚚 Order dispatched")
    if state.status == DealStatus.INVOICE_FAILED:
        trail.append("⚠️ Invoice generation failed — needs manual retry")

    return trail
