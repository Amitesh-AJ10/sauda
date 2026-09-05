"""Thin wrapper around Razorpay's Payment Links and Invoices APIs (raw HTTPS,
no SDK).

Kept deliberately small, same shape as `WhatsAppService`: nodes depend only
on `create_payment_link` / `create_invoice`, so tests can swap in a fake
without ever hitting the network.
"""

import hashlib
import hmac
import os
from functools import lru_cache

import httpx
from pydantic import BaseModel

from app.agent.state import DealState

RAZORPAY_API_BASE_URL = "https://api.razorpay.com/v1"


class PaymentLink(BaseModel):
    id: str
    short_url: str
    status: str


class Invoice(BaseModel):
    id: str
    short_url: str
    status: str


class RazorpayClient:
    def __init__(self, key_id: str | None = None, key_secret: str | None = None) -> None:
        self._key_id = key_id or os.environ.get("RAZORPAY_KEY_ID")
        self._key_secret = key_secret or os.environ.get("RAZORPAY_KEY_SECRET")

    def create_payment_link(self, amount_paise: int, description: str, notes: dict) -> PaymentLink:
        """Create a payment link for `amount_paise` (INR, in paise)."""
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "description": description,
            "notes": notes,
        }
        response = httpx.post(
            f"{RAZORPAY_API_BASE_URL}/payment_links",
            json=payload,
            auth=(self._key_id or "", self._key_secret or ""),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return PaymentLink(id=data["id"], short_url=data["short_url"], status=data["status"])

    def create_invoice(self, deal: DealState) -> Invoice:
        """Create a GST-compliant invoice for a paid deal.

        `unit_price * qty` (in paise) is taken straight from the deterministic
        `DealState` fields set earlier in the graph — never recomputed or
        guessed here.
        """
        qty = deal.qty or 0
        unit_price_paise = round((deal.unit_price or 0.0) * 100)
        payload = {
            "type": "invoice",
            "description": f"Invoice for {qty} x {deal.item_name}",
            "customer": {"name": deal.hospital_name or ""},
            "line_items": [
                {
                    "name": deal.item_name or "",
                    "amount": unit_price_paise,
                    "currency": "INR",
                    "quantity": qty,
                }
            ],
            "currency": "INR",
            "notes": {"pin_code": deal.pin_code or ""},
        }
        response = httpx.post(
            f"{RAZORPAY_API_BASE_URL}/invoices",
            json=payload,
            auth=(self._key_id or "", self._key_secret or ""),
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return Invoice(id=data["id"], short_url=data["short_url"], status=data["status"])


def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify `X-Razorpay-Signature`: HMAC-SHA256 of the raw body, keyed by the webhook secret."""
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@lru_cache
def get_razorpay_client() -> RazorpayClient:
    return RazorpayClient()
