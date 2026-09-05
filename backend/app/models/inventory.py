from pydantic import BaseModel


class InventoryItem(BaseModel):
    product_id: str
    item_name: str
    stock_qty: int
    base_price: float
    notes: str
