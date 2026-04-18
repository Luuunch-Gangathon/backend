from tests.conftest import get


def test_list_companies_returns_61(api):
    r = get(api, "/companies")
    assert r.status_code == 200
    assert len(r.json()) == 61


def test_list_companies_schema(api):
    r = get(api, "/companies")
    for item in r.json():
        assert isinstance(item["id"], int)
        assert isinstance(item["name"], str)


def test_get_company_1(api):
    r = get(api, "/companies/1")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "name": "21st Century"}


def test_get_company_not_found(api):
    r = get(api, "/companies/99999")
    assert r.status_code == 404
