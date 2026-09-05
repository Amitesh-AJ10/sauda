from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_inventory_returns_all_items():
    response = client.get("/inventory")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) >= 20
    assert {"product_id", "item_name", "stock_qty", "base_price", "notes"} <= body[0].keys()


def test_get_inventory_item_found():
    response = client.get("/inventory/Pulse Oximeter")
    assert response.status_code == 200
    body = response.json()
    assert body["item_name"] == "Pulse Oximeter"


def test_get_inventory_item_not_found():
    response = client.get("/inventory/flux-capacitor-9000")
    assert response.status_code == 404
