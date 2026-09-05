import csv
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

from app.models.inventory import InventoryItem

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "mock_inventory.csv"

FUZZY_MATCH_THRESHOLD = 0.6


class InventoryService:
    """Deterministic source of truth for stock and pricing.

    Loads the mock CSV once and caches it in memory. The LLM must never
    invent stock or price data — it only ever reads through this service.
    """

    def __init__(self, csv_path: Path = DATA_PATH) -> None:
        self._csv_path = csv_path
        self._items: list[InventoryItem] = self._load()

    def _load(self) -> list[InventoryItem]:
        with self._csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [
                InventoryItem(
                    product_id=row["product_id"],
                    item_name=row["item_name"],
                    stock_qty=int(row["stock_qty"]),
                    base_price=float(row["base_price"]),
                    notes=row["notes"],
                )
                for row in reader
            ]

    def all_items(self) -> list[InventoryItem]:
        return list(self._items)

    def find(self, item_name: str) -> InventoryItem | None:
        """Case-insensitive lookup by exact match, substring, then fuzzy match."""
        query = item_name.strip().lower()
        if not query:
            return None

        for item in self._items:
            if item.item_name.lower() == query:
                return item

        for item in self._items:
            if query in item.item_name.lower():
                return item

        best_item: InventoryItem | None = None
        best_score = 0.0
        for item in self._items:
            score = SequenceMatcher(None, query, item.item_name.lower()).ratio()
            if score > best_score:
                best_score = score
                best_item = item

        if best_score >= FUZZY_MATCH_THRESHOLD:
            return best_item
        return None

    def has_stock(self, item_name: str, qty: int) -> bool:
        item = self.find(item_name)
        if item is None:
            return False
        return item.stock_qty >= qty


@lru_cache
def get_inventory_service() -> InventoryService:
    return InventoryService()
