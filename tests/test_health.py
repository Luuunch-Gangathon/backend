from tests.conftest import get


def test_health(api):
    r = get(api, "/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
