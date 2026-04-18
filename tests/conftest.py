import pytest
import requests

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def api():
    """Plain HTTP session pointing at running server."""
    s = requests.Session()
    s.base_url = BASE_URL
    # Verify server is up
    r = s.get(f"{BASE_URL}/health")
    assert r.status_code == 200, f"Server not running at {BASE_URL}"
    yield s
    s.close()


def get(api, path):
    return api.get(f"{api.base_url}{path}")
