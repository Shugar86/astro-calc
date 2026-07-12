"""Bootstrap golden-chart fixtures from the current kerykeion output.

These values are a *regression baseline*, not ground truth: they lock the engine
against silent drift. Per spec §4.4 they must be verified by hand against
astro.com and replaced with the confirmed degrees (flip
``verified_against_astro_com`` to true then). The test structure and tolerances
do not change when the numbers are swapped.

Run:  uv run python scripts/gen_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import engine_versions
from app.engine import build_natal
from app.schemas import NatalRequest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

# 5 reference charts. >=2 births in the USSR 1970-1995 (historical timezones /
# decree time) are mandatory; here 3 (Kazan-88, Leningrad-75, Novosibirsk-82),
# plus a post-USSR Russian chart and a western-hemisphere DST-era chart.
CHARTS: list[dict] = [
    {
        "slug": "kazan-1988",
        "input": {"name": "Kazan 1988", "dt_utc": "1988-03-14T09:30:00Z",
                  "lat": 55.7887, "lng": 49.1221, "tz": "Europe/Moscow"},
    },
    {
        "slug": "leningrad-1975",
        "input": {"name": "Leningrad 1975", "dt_utc": "1975-06-20T04:15:00Z",
                  "lat": 59.9375, "lng": 30.3086, "tz": "Europe/Moscow"},
    },
    {
        "slug": "novosibirsk-1982",
        "input": {"name": "Novosibirsk 1982", "dt_utc": "1982-12-01T16:45:00Z",
                  "lat": 55.0084, "lng": 82.9357, "tz": "Asia/Novosibirsk"},
    },
    {
        "slug": "moscow-1993",
        "input": {"name": "Moscow 1993", "dt_utc": "1993-09-09T12:20:00Z",
                  "lat": 55.7558, "lng": 37.6173, "tz": "Europe/Moscow"},
    },
    {
        "slug": "newyork-2001",
        "input": {"name": "New York 2001", "dt_utc": "2001-05-05T07:05:00Z",
                  "lat": 40.7128, "lng": -74.0060, "tz": "America/New_York"},
    },
]


def _aspect_key(a: str, b: str, kind: str) -> str:
    """Order-independent key for a major aspect."""
    lo, hi = sorted((a, b))
    return f"{lo}|{hi}|{kind}"


def build_expected(inp: dict) -> dict:
    """Compute the expected block (points, houses, aspects) for one chart."""
    resp = build_natal(NatalRequest(**inp))
    return {
        "points": {p.id: p.abs_deg for p in resp.points},
        "houses": {str(h.n): h.cusp_abs_deg for h in resp.houses},
        "aspects": sorted(_aspect_key(a.a, a.b, a.type) for a in resp.aspects),
    }


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    versions = engine_versions()
    for chart in CHARTS:
        fixture = {
            "slug": chart["slug"],
            "note": (
                f"Bootstrap baseline from kerykeion {versions['kerykeion']} / "
                f"sweph {versions['sweph']}. PENDING manual verification against "
                "astro.com (spec 4.4). Replace `expected` with astro.com-confirmed "
                "degrees and set verified_against_astro_com=true; tolerances stay."
            ),
            "verified_against_astro_com": False,
            "tolerances": {"point_abs_deg": 0.01, "house_cusp_abs_deg": 0.05},
            "input": chart["input"],
            "expected": build_expected(chart["input"]),
        }
        path = FIXTURES_DIR / f"{chart['slug']}.json"
        path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(FIXTURES_DIR.parent.parent)} "
              f"({len(fixture['expected']['aspects'])} aspects)")


if __name__ == "__main__":
    main()
