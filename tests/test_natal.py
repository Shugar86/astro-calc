"""Behavioural tests for /v1/natal and /v1/synastry."""

from __future__ import annotations

from xml.etree import ElementTree

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


def test_natal_svg_escapes_subject_name(client: TestClient) -> None:
    name = "</title><script>alert('xss') & more</script><title>"

    for variant in ("wheel", "full"):
        r = client.post(
            "/v1/natal",
            json={**BODY, "name": name, "with_svg": True, "svg_variant": variant},
        )
        assert r.status_code == 200
        svg = r.json()["svg"]
        root = ElementTree.fromstring(svg)
        title = root.find("{http://www.w3.org/2000/svg}title")

        assert title is not None
        assert title.text == f"{name} - Birth Chart"
        assert not any(node.tag.endswith("script") for node in root.iter())
        assert "<script" not in svg.lower()


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


def test_natal_rejects_invalid_timezone(client: TestClient) -> None:
    r = client.post("/v1/natal", json={**BODY, "tz": "Invalid/Nowhere"})

    assert r.status_code == 422


def test_natal_rejects_naive_datetime(client: TestClient) -> None:
    r = client.post("/v1/natal", json={**BODY, "dt_utc": "1988-03-14T09:30:00"})

    assert r.status_code == 422


def test_angles_are_independent_of_house_system(client: TestClient) -> None:
    responses = {
        house_system: client.post(
            "/v1/natal", json={**BODY, "house_system": house_system}
        )
        for house_system in ("placidus", "whole_sign", "equal")
    }

    assert all(response.status_code == 200 for response in responses.values())
    bodies = {name: response.json() for name, response in responses.items()}
    assert all(len(body["points"]) == 13 for body in bodies.values())
    assert bodies["whole_sign"]["angles"] == bodies["placidus"]["angles"]
    assert bodies["equal"]["angles"] == bodies["placidus"]["angles"]


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
