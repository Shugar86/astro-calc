"""Golden-chart regression: the engine must not drift from the locked baselines.

Fixtures are bootstrapped from kerykeion and PENDING manual verification against
astro.com (see scripts/gen_fixtures.py and each fixture's `note`). Tolerances
live in the fixture: 0.01 deg for point longitudes, 0.05 deg for house cusps.
Any drift beyond tolerance fails the test.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engine import build_natal
from app.schemas import NatalRequest

FIXTURES = sorted((Path(__file__).parent / "fixtures").glob("*.json"))


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _angular_diff(a: float, b: float) -> float:
    """Smallest absolute difference between two ecliptic longitudes (mod 360)."""
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _aspect_key(a: str, b: str, kind: str) -> str:
    lo, hi = sorted((a, b))
    return f"{lo}|{hi}|{kind}"


assert FIXTURES, "no golden fixtures found — run scripts/gen_fixtures.py"


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_golden_chart(path: Path) -> None:
    fx = _load(path)
    tol = fx["tolerances"]
    resp = build_natal(NatalRequest(**fx["input"]))

    got_points = {p.id: p.abs_deg for p in resp.points}
    for pid, expected_deg in fx["expected"]["points"].items():
        assert pid in got_points, f"{path.stem}: missing point {pid}"
        drift = _angular_diff(got_points[pid], expected_deg)
        assert drift <= tol["point_abs_deg"], (
            f"{path.stem}: {pid} drifted {drift:.4f} deg "
            f"(> {tol['point_abs_deg']}); got {got_points[pid]}, want {expected_deg}"
        )

    got_houses = {str(h.n): h.cusp_abs_deg for h in resp.houses}
    for n, expected_deg in fx["expected"]["houses"].items():
        drift = _angular_diff(got_houses[n], expected_deg)
        assert drift <= tol["house_cusp_abs_deg"], (
            f"{path.stem}: cusp {n} drifted {drift:.4f} deg "
            f"(> {tol['house_cusp_abs_deg']})"
        )

    got_aspects = sorted(_aspect_key(a.a, a.b, a.type) for a in resp.aspects)
    assert got_aspects == sorted(fx["expected"]["aspects"]), (
        f"{path.stem}: major-aspect list changed"
    )
