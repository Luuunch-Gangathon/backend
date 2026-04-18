from tests.conftest import get


def test_list_suppliers_returns_40(api):
    r = get(api, "/suppliers")
    assert r.status_code == 200
    assert len(r.json()) == 40


def test_list_suppliers_schema(api):
    r = get(api, "/suppliers")
    for item in r.json():
        assert isinstance(item["id"], int)
        assert isinstance(item["name"], str)


def test_get_supplier_1(api):
    r = get(api, "/suppliers/1")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "name": "ADM"}


def test_get_supplier_not_found(api):
    r = get(api, "/suppliers/99999")
    assert r.status_code == 404
