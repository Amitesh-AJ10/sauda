"""Fixed hospital directory for the chat-driven demo surface.

Five real counterparties (mocked identities, real everything else) so the
merchant dashboard always has a stable set of tiles to show, and the
hospital-facing chat page (`/hospital/<id>`) has something to be. Every
message any of them sends runs through the real agent graph, real
inventory lookup, and real Razorpay client — only the buyer's identity is
hardcoded, not the outcome.
"""

from pydantic import BaseModel


class Hospital(BaseModel):
    id: str
    name: str
    pin_code: str


HOSPITALS: list[Hospital] = [
    Hospital(id="city-care", name="City Care Hospital", pin_code="411001"),
    Hospital(id="apollo-north", name="Apollo North", pin_code="560001"),
    Hospital(id="sunrise-multispecialty", name="Sunrise Multispecialty", pin_code="110001"),
    Hospital(id="st-marys", name="St. Mary's Medical Center", pin_code="600001"),
    Hospital(id="green-valley", name="Green Valley Clinic", pin_code="500001"),
]

_BY_ID = {hospital.id: hospital for hospital in HOSPITALS}


def get_hospital(hospital_id: str) -> Hospital | None:
    return _BY_ID.get(hospital_id)


def list_hospitals() -> list[Hospital]:
    return HOSPITALS
