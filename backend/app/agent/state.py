from enum import StrEnum

from pydantic import BaseModel, Field


class DealStatus(StrEnum):
    """The six-stage deal lifecycle, plus two terminal short-circuits."""

    EXTRACTING_INTENT = "extracting_intent"
    CHECKING_INVENTORY = "checking_inventory"
    NEGOTIATING = "negotiating"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    ISSUING_INVOICE = "issuing_invoice"
    DISPATCHED = "dispatched"
    OUT_OF_STOCK = "out_of_stock"
    DECLINED = "declined"
    INVOICE_FAILED = "invoice_failed"


class ExtractedIntent(BaseModel):
    """Structured output the LLM must produce when reading a buyer message."""

    item_name: str | None = None
    qty: int | None = None
    hospital_name: str | None = None
    pin_code: str | None = None
    # True unless the message is clearly unrelated to ordering/quoting
    # medical/surgical supplies — lets the graph redirect gracefully
    # instead of forcing extraction on a stray off-topic message.
    on_topic: bool = True


class DealState(BaseModel):
    """The single source of truth threaded through every LangGraph node.

    The LLM only ever reads/writes the *language* fields (buyer-facing
    `reply`, and the structured `ExtractedIntent` it's asked to produce).
    Every field that touches money or stock (`unit_price`, `available_qty`,
    `status`) is set exclusively by Python node logic.
    """

    messages: list[str] = Field(default_factory=list)

    item_name: str | None = None
    qty: int | None = None
    hospital_name: str | None = None
    pin_code: str | None = None

    unit_price: float | None = None
    available_qty: int | None = None

    payment_link_id: str | None = None
    payment_link_url: str | None = None
    invoice_url: str | None = None

    status: DealStatus = DealStatus.EXTRACTING_INTENT
    reply: str | None = None

    guardrail_violations: list[str] = Field(default_factory=list)

    # Transient one-turn routing signals, set by `interpret_reply` and read
    # by the graph's edge function right after — never meant to be read
    # once the turn finishes. Not part of any API response model.
    just_confirmed: bool = False
    handled: bool = False
    off_topic: bool = False
