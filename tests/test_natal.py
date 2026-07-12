"""Behavioural tests for /v1/natal and /v1/synastry."""

from __future__ import annotations

from fastapi.testclient import TestClient

BODY = {
    "name": "Елена",
    "dt_utc": "1988-03-14T09:30:00Z",
    "lat": 55.7887,
    "lng": 49.1221,
    "tz": "Europe/Moscow",
}


def test_natal_full(client: TestClient) -> None:
    r = client.post("/v1/natal", json=BODY)
    assert r.status_code == 200
    body = r.json()
    assert len(body["points"]) == 13
    assert len(body["houses"]) == 12
    assert set(body["angles"]) == {"asc", "mc"}
    assert body["meta"]["time_unknown"] is False
    # distributions are integer counts over the 10 classical planets
    assert sum(body["distributions"]["elements"].values()) == 10
    assert sum(body["distributions"]["qualities"].values()) == 10
    # svg omitted unless requested
    assert "svg" not in body


def test_natal_with_svg(client: TestClient) -> None:
    r = client.post("/v1/natal", json={**BODY, "with_svg": True, "svg_variant": "wheel"})
    assert r.status_code == 200
    svg = r.json()["svg"]
    assert svg.strip().endswith("</svg>")
    assert "var(--kerykeion" in svg  # CSS-variable themable output


def test_natal_noon_no_houses(client: TestClient) -> None:
    r = client.post("/v1/natal", json={**BODY, "houses_mode": "noon_no_houses"})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["time_unknown"] is True
    assert "houses" not in body
    assert "angles" not in body
    # points still present, but without a house assignment
    assert all("house" not in p for p in body["points"])


def test_natal_validation_error(client: TestClient) -> None:
    r = client.post("/v1/natal", json={**BODY, "lat": 999})
    assert r.status_code == 422


def test_synastry_scaffold(client: TestClient) -> None:
    second = {
        "name": "Иван",
        "dt_utc": "1985-11-02T14:00:00Z",
        "lat": 55.7558,
        "lng": 37.6173,
        "tz": "Europe/Moscow",
    }
    r = client.post("/v1/synastry", json={"first": BODY, "second": second})
    assert r.status_code == 200
    assert isinstance(r.json()["aspects"], list)
