from app.agent.catalog import pack_size


def test_pack_size_parses_box_of_n():
    assert pack_size("Nitrile Examination Gloves (Box of 100)") == 100
    assert pack_size("Disposable Syringe 5ml (Box of 100)") == 100
    assert pack_size("Foley Catheter 16Fr (Box of 10)") == 10


def test_pack_size_none_for_a_loose_item():
    assert pack_size("Pulse Oximeter") is None
    assert pack_size("Surgical Scissors (Reusable)") is None


def test_pack_size_case_insensitive():
    assert pack_size("Some Item (box of 25)") == 25
