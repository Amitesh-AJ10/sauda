from fastapi import FastAPI, HTTPException

from app.models.inventory import InventoryItem
from app.services.inventory import get_inventory_service

app = FastAPI(title="Sauda")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/inventory")
def list_inventory() -> list[InventoryItem]:
    """Debug/admin endpoint: list all inventory items."""
    return get_inventory_service().all_items()


@app.get("/inventory/{item_name}")
def get_inventory_item(item_name: str) -> InventoryItem:
    """Debug/admin endpoint: look up a single item by (fuzzy) name."""
    item = get_inventory_service().find(item_name)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
