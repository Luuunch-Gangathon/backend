from tests.conftest import get


def test_list_products_returns_149(api):
    r = get(api, "/products")
    assert r.status_code == 200
    assert len(r.json()) == 149


def test_list_products_schema(api):
    r = get(api, "/products")
    for item in r.json():
        assert isinstance(item["id"], int)
        assert isinstance(item["sku"], str)
        assert isinstance(item["company_id"], int)


def test_list_products_filter_by_company(api):
    r = get(api, "/products?company_id=28")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    assert all(item["company_id"] == 28 for item in data)


def test_list_products_filter_empty(api):
    r = get(api, "/products?company_id=99999")
    assert r.status_code == 200
    assert r.json() == []


def test_get_product_1(api):
    r = get(api, "/products/1")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert data["sku"] == "FG-iherb-10421"
    assert data["company_id"] == 28


def test_get_product_not_found(api):
    r = get(api, "/products/99999")
    assert r.status_code == 404


def test_get_bom_product_1(api):
    r = get(api, "/products/1/bom")
    assert r.status_code == 200
    data = r.json()
    assert data["produced_product_id"] == 1
    assert isinstance(data["consumed_raw_material_ids"], list)
    for rm_id in [506, 509, 511, 512]:
        assert rm_id in data["consumed_raw_material_ids"]


def test_get_bom_not_found(api):
    r = get(api, "/products/99999/bom")
    assert r.status_code == 404
