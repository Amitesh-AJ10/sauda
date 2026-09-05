import os
from functools import lru_cache

import httpx

GRAPH_API_VERSION = "v20.0"
GRAPH_API_BASE_URL = "https://graph.facebook.com"


class WhatsAppService:
    """Thin wrapper around the WhatsApp Cloud API's `/messages` endpoint."""

    def __init__(self, token: str | None = None, phone_number_id: str | None = None) -> None:
        self._token = token or os.environ.get("WHATSAPP_TOKEN")
        self._phone_number_id = phone_number_id or os.environ.get("WHATSAPP_PHONE_NUMBER_ID")

    def send_message(self, to: str, text: str) -> dict:
        """Send a plain-text WhatsApp message to `to`."""
        url = f"{GRAPH_API_BASE_URL}/{GRAPH_API_VERSION}/{self._phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        headers = {"Authorization": f"Bearer {self._token}"}
        response = httpx.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()


@lru_cache
def get_whatsapp_service() -> WhatsAppService:
    return WhatsAppService()
