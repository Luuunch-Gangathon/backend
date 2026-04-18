from tests.conftest import get


def test_list_raw_materials_returns_876(api):
    r = get(api, "/raw-materials")
    assert r.status_code == 200
    assert len(r.json()) == 876


def test_list_raw_materials_schema(api):
    r = get(api, "/raw-materials")
    for item in r.json():
        assert isinstance(item["id"], int)
        assert isinstance(item["sku"], str)
        assert isinstance(item["suppliers_count"], int)
        assert isinstance(item["used_products_count"], int)


def test_get_raw_material_150(api):
    r = get(api, "/raw-materials/150")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 150
    assert body["sku"] == "RM-C1-calcium-citrate-05c28cc3"
    assert isinstance(body["suppliers_count"], int)
    assert isinstance(body["used_products_count"], int)


def test_get_raw_material_not_found(api):
    r = get(api, "/raw-materials/99999")
    assert r.status_code == 404
