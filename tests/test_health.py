"""Health endpoint contract."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert set(body["versions"]) == {"kerykeion", "sweph"}
    assert body["calc_version"]
