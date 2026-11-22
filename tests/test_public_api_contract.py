"""Smoke checks for the public web API without external credentials/network."""
from fastapi.testclient import TestClient

from api_server import app

client = TestClient(app)


def test_health_and_public_metadata():
    result = client.get("/api/health")
    assert result.status_code == 200
    assert result.json()["status"] == "ok"


def test_reject_unrelated_url_before_api_use():
    result = client.post("/api/verify", json={"url": "https://example.org/not-youtube"})
    assert result.status_code == 400


def test_no_secrets_on_sources_endpoint():
    result = client.get("/api/sources")
    assert result.status_code == 200
    value = result.json()
    assert value["count"] >= 1
    assert "api_key" not in value
