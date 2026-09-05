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


class ExtractedIntent(BaseModel):
    """Structured output the LLM must produce when reading a buyer message."""

    item_name: str | None = None
    qty: int | None = None
    hospital_name: str | None = None
    pin_code: str | None = None


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

    status: DealStatus = DealStatus.EXTRACTING_INTENT
    reply: str | None = None

    guardrail_violations: list[str] = Field(default_factory=list)
