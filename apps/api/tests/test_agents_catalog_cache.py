import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_agents_list_has_cache_metadata(client):
    r = client.get("/api/agents/list")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "agents" in data
    assert "source" in data
    # optional metadata
    assert "last_refreshed" in data
    assert "refresh_in_progress" in data


def test_agents_list_refresh_trigger(client):
    r = client.get("/api/agents/list?refresh=true")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "agents" in data
    assert "source" in data

