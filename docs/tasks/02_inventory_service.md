# Task 02 — Inventory Service

Parent: [../PRD.md](../PRD.md) · Depends on: [01_project_setup](./01_project_setup.md)

## Goal

A deterministic source of truth for stock and pricing that the agent (and no one else) reads from — the LLM must never invent stock.

## Scope

- `backend/app/data/mock_inventory.csv` with columns: `product_id, item_name, stock_qty, base_price, notes`. Seed with ~8-10 realistic surgical-supply rows (gloves, staplers, syringes, etc.) including a `notes` field with grounded specs (e.g., "Nitrile, Powder-free, Latex-free").
- `backend/app/models/inventory.py` — Pydantic model `InventoryItem` matching the CSV schema.
- `backend/app/services/inventory.py` — a small `InventoryService` that:
  - Loads the CSV once (cached in memory).
  - `find(item_name: str) -> InventoryItem | None` (case-insensitive, simple substring/fuzzy match).
  - `has_stock(item_name: str, qty: int) -> bool`.
- `backend/app/main.py` — add `GET /inventory` (list all items) and `GET /inventory/{item_name}` (lookup one) for manual verification. These are debug/admin endpoints, not the buyer-facing API (that's Task 08).

## Out of Scope

- Any LLM involvement.
- Stock mutation/decrement logic (can be a follow-up once payments land).

## Acceptance Criteria

- [x] `GET /inventory` returns all rows as JSON matching `InventoryItem`.
- [x] `GET /inventory/{item_name}` returns `404` for an unknown item, `200` with the item otherwise.
- [x] `InventoryService.has_stock` correctly compares requested qty against `stock_qty`.

## Tests

- Unit tests for `InventoryService.find` and `has_stock` (known item, unknown item, exact qty boundary, over-stock request).
- API tests for both endpoints (found / not-found cases).
