from app.services.inventory import InventoryService


def make_service() -> InventoryService:
    return InventoryService()


def test_find_known_item_exact_case_insensitive():
    service = make_service()
    item = service.find("nitrile examination gloves (box of 100)")
    assert item is not None
    assert item.product_id == "SUR-001"


def test_find_known_item_substring():
    service = make_service()
    item = service.find("pulse oximeter")
    assert item is not None
    assert item.item_name == "Pulse Oximeter"


def test_find_unknown_item_returns_none():
    service = make_service()
    assert service.find("flux capacitor") is None


def test_has_stock_exact_qty_boundary():
    service = make_service()
    item = service.find("Nitrile Examination Gloves (Box of 100)")
    assert item is not None
    assert service.has_stock(item.item_name, item.stock_qty) is True


def test_has_stock_over_stock_request():
    service = make_service()
    item = service.find("Nitrile Examination Gloves (Box of 100)")
    assert item is not None
    assert service.has_stock(item.item_name, item.stock_qty + 1) is False


def test_has_stock_unknown_item_is_false():
    service = make_service()
    assert service.has_stock("flux capacitor", 1) is False


def test_has_stock_zero_stock_item():
    service = make_service()
    item = service.find("Foley Catheter 16Fr (Box of 10)")
    assert item is not None
    assert item.stock_qty == 0
    assert service.has_stock(item.item_name, 1) is False
