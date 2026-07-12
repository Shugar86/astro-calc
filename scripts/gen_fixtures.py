"""Regenerate golden fixtures from the direct pyswisseph oracle.

The generator does not call ``app.engine`` or Kerykeion calculation code.  The
service regression in ``tests/test_golden.py`` therefore compares one code path
with a separately produced reference.

Run from the repository root::

    uv run python scripts/gen_fixtures.py
    uv run python scripts/verify_fixtures.py
"""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path

import swisseph as swe

from scripts.verify_fixtures import calculate_reference

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

# Five reference charts.  Three dates are births in the historical USSR, more
# than the acceptance minimum of two.  ``dt_utc`` is already an unambiguous
# instant; the IANA timezone remains part of the public service request.
CHARTS: list[dict] = [
    {
        "slug": "kazan-1988",
        "historical_ussr": True,
        "input": {
            "name": "Kazan 1988",
            "dt_utc": "1988-03-14T09:30:00Z",
            "lat": 55.7887,
            "lng": 49.1221,
            "tz": "Europe/Moscow",
        },
    },
    {
        "slug": "leningrad-1975",
        "historical_ussr": True,
        "input": {
            "name": "Leningrad 1975",
            "dt_utc": "1975-06-20T04:15:00Z",
            "lat": 59.9375,
            "lng": 30.3086,
            "tz": "Europe/Moscow",
        },
    },
    {
        "slug": "novosibirsk-1982",
        "historical_ussr": True,
        "input": {
            "name": "Novosibirsk 1982",
            "dt_utc": "1982-12-01T16:45:00Z",
            "lat": 55.0084,
            "lng": 82.9357,
            "tz": "Asia/Novosibirsk",
        },
    },
    {
        "slug": "moscow-1993",
        "historical_ussr": False,
        "input": {
            "name": "Moscow 1993",
            "dt_utc": "1993-09-09T12:20:00Z",
            "lat": 55.7558,
            "lng": 37.6173,
            "tz": "Europe/Moscow",
        },
    },
    {
        "slug": "newyork-2001",
        "historical_ussr": False,
        "input": {
            "name": "New York 2001",
            "dt_utc": "2001-05-05T07:05:00Z",
            "lat": 40.7128,
            "lng": -74.0060,
            "tz": "America/New_York",
        },
    },
]


def build_expected(chart_input: dict) -> dict:
    """Calculate and round the committed reference values."""
    reference = calculate_reference(chart_input)
    return {
        "points": {
            point_id: round(longitude, 4)
            for point_id, longitude in reference["points"].items()
        },
        "houses": {
            house_number: round(longitude, 4)
            for house_number, longitude in reference["houses"].items()
        },
        "aspects": reference["aspects"],
    }


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    pyswisseph_version = importlib.metadata.version("pyswisseph")
    for chart in CHARTS:
        fixture = {
            "slug": chart["slug"],
            "note": (
                f"Reference values verified directly through pyswisseph {pyswisseph_version} / "
                f"Swiss Ephemeris {swe.version}; no app.engine or kerykeion calculation "
                "code is used."
            ),
            "verified_against_swiss_ephemeris_direct": True,
            "verification_method": "scripts/verify_fixtures.py",
            "historical_ussr": chart["historical_ussr"],
            "tolerances": {"point_abs_deg": 0.01, "house_cusp_abs_deg": 0.05},
            "input": chart["input"],
            "expected": build_expected(chart["input"]),
        }
        path = FIXTURES_DIR / f"{chart['slug']}.json"
        path.write_text(
            json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"wrote {path.relative_to(FIXTURES_DIR.parent.parent)} "
            f"({len(fixture['expected']['aspects'])} aspects)"
        )


if __name__ == "__main__":
    main()
