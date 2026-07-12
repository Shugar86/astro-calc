"""Verify the five golden charts directly with the pyswisseph API.

This module deliberately does not import ``app`` or ``kerykeion`` calculation
code.  It is the independent numerical oracle for the service regression
fixtures.  Kerykeion's installed ephemeris *data directory* is located without
importing the package because it contains the Chiron file required by Swiss
Ephemeris.

Run from the repository root::

    uv run python scripts/verify_fixtures.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import swisseph as swe

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FIXTURES_DIR = REPOSITORY_ROOT / "tests" / "fixtures"
EXPECTED_FIXTURE_COUNT = 5
MIN_USSR_FIXTURE_COUNT = 2
USSR_FIRST_DAY = date(1922, 12, 30)
USSR_LAST_DAY = date(1991, 12, 26)

# Stable API ids -> native Swiss Ephemeris body ids.  These constants are kept
# here rather than imported from app.config so the oracle remains independent
# from the implementation it verifies.
POINT_BODIES: dict[str, int] = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "chiron": swe.CHIRON,
    "lilith": swe.MEAN_APOG,
    "north_node": swe.MEAN_NODE,
}

# (public name, exact angle, allowed orb).  This is also intentionally copied
# from the public contract rather than imported from app.config.
MAJOR_ASPECTS: tuple[tuple[str, float, float], ...] = (
    ("conjunction", 0.0, 10.0),
    ("opposition", 180.0, 10.0),
    ("trine", 120.0, 8.0),
    ("square", 90.0, 5.0),
    ("sextile", 60.0, 6.0),
)

CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


class FixtureVerificationError(AssertionError):
    """Raised when a committed fixture differs from the direct oracle."""


@dataclass(frozen=True)
class VerificationSummary:
    """Counts emitted after a complete successful verification run."""

    fixture_count: int
    ussr_fixture_count: int
    point_count: int
    house_count: int
    aspect_count: int


def _ephemeris_path() -> Path:
    """Find the data files used by Swiss Ephemeris without importing Kerykeion."""
    if configured := os.environ.get("SE_EPHE_PATH"):
        path = Path(configured).expanduser().resolve()
    else:
        spec = importlib.util.find_spec("kerykeion")
        locations = tuple(spec.submodule_search_locations or ()) if spec else ()
        path = Path(locations[0]) / "sweph" if locations else Path()

    if not path.is_dir():
        raise FixtureVerificationError(
            "Swiss Ephemeris data directory not found; install dependencies or set SE_EPHE_PATH"
        )
    if not (path / "seas_18.se1").is_file():
        raise FixtureVerificationError(f"Chiron ephemeris file seas_18.se1 missing in {path}")
    return path


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise FixtureVerificationError(f"dt_utc must be timezone-aware: {value!r}")
    return parsed.astimezone(timezone.utc)


def _julian_day(dt_utc: datetime) -> float:
    hour = (
        dt_utc.hour
        + dt_utc.minute / 60.0
        + dt_utc.second / 3600.0
        + dt_utc.microsecond / 3_600_000_000.0
    )
    return swe.julday(
        dt_utc.year,
        dt_utc.month,
        dt_utc.day,
        hour,
        swe.GREG_CAL,
    )


def _angular_diff(first: float, second: float) -> float:
    difference = abs(first - second) % 360.0
    return min(difference, 360.0 - difference)


def _aspect_key(first: str, second: str, kind: str) -> str:
    low, high = sorted((first, second))
    return f"{low}|{high}|{kind}"


def _calculate_aspects(points: dict[str, float]) -> list[str]:
    aspects: list[str] = []
    for first, second in combinations(points, 2):
        separation = _angular_diff(points[first], points[second])
        for kind, exact_angle, orb in MAJOR_ASPECTS:
            if abs(separation - exact_angle) <= orb:
                aspects.append(_aspect_key(first, second, kind))
                break
    return sorted(aspects)


def calculate_reference(chart_input: dict[str, Any]) -> dict[str, Any]:
    """Calculate one tropical/Placidus reference through pyswisseph only."""
    if chart_input.get("zodiac", "tropical") != "tropical":
        raise FixtureVerificationError("direct fixture oracle currently supports tropical only")
    if chart_input.get("house_system", "placidus") != "placidus":
        raise FixtureVerificationError("direct fixture oracle currently supports Placidus only")

    dt_utc = _parse_utc(chart_input["dt_utc"])
    julian_day = _julian_day(dt_utc)

    swe.set_ephe_path(str(_ephemeris_path()))
    try:
        points = {
            point_id: swe.calc_ut(julian_day, body_id, CALC_FLAGS)[0][0]
            for point_id, body_id in POINT_BODIES.items()
        }
        houses, _ = swe.houses_ex(
            julian_day,
            float(chart_input["lat"]),
            float(chart_input["lng"]),
            b"P",
            CALC_FLAGS,
        )
    finally:
        swe.close()

    return {
        "points": points,
        "houses": {str(number): value for number, value in enumerate(houses, start=1)},
        "aspects": _calculate_aspects(points),
    }


def _load_fixture(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise FixtureVerificationError(f"cannot load {path}: {error}") from error


def verify_fixture(path: Path) -> tuple[int, int, int]:
    """Verify metadata and every numerical field in a single fixture."""
    fixture = _load_fixture(path)
    label = fixture.get("slug", path.stem)

    if fixture.get("verified_against_swiss_ephemeris_direct") is not True:
        raise FixtureVerificationError(
            f"{label}: verified_against_swiss_ephemeris_direct must be true"
        )

    expected = fixture.get("expected", {})
    expected_points = expected.get("points", {})
    expected_houses = expected.get("houses", {})
    expected_aspects = expected.get("aspects", [])

    if set(expected_points) != set(POINT_BODIES):
        missing = sorted(set(POINT_BODIES) - set(expected_points))
        extra = sorted(set(expected_points) - set(POINT_BODIES))
        raise FixtureVerificationError(f"{label}: point set mismatch; missing={missing}, extra={extra}")
    required_houses = {str(number) for number in range(1, 13)}
    if set(expected_houses) != required_houses:
        raise FixtureVerificationError(f"{label}: house cusps must be exactly 1..12")
    if len(expected_aspects) != len(set(expected_aspects)):
        raise FixtureVerificationError(f"{label}: duplicate aspect keys")

    tolerances = fixture.get("tolerances", {})
    try:
        point_tolerance = float(tolerances["point_abs_deg"])
        house_tolerance = float(tolerances["house_cusp_abs_deg"])
    except (KeyError, TypeError, ValueError) as error:
        raise FixtureVerificationError(f"{label}: invalid tolerances") from error

    reference = calculate_reference(fixture["input"])
    for point_id, direct_value in reference["points"].items():
        drift = _angular_diff(float(expected_points[point_id]), direct_value)
        if drift > point_tolerance:
            raise FixtureVerificationError(
                f"{label}: {point_id} differs from direct Swiss Ephemeris by "
                f"{drift:.6f}° (limit {point_tolerance}°)"
            )

    for house_number, direct_value in reference["houses"].items():
        drift = _angular_diff(float(expected_houses[house_number]), direct_value)
        if drift > house_tolerance:
            raise FixtureVerificationError(
                f"{label}: house {house_number} differs from direct Swiss Ephemeris by "
                f"{drift:.6f}° (limit {house_tolerance}°)"
            )

    if sorted(expected_aspects) != reference["aspects"]:
        missing = sorted(set(reference["aspects"]) - set(expected_aspects))
        extra = sorted(set(expected_aspects) - set(reference["aspects"]))
        raise FixtureVerificationError(
            f"{label}: major aspect list mismatch; missing={missing}, extra={extra}"
        )

    return len(expected_points), len(expected_houses), len(expected_aspects)


def verify_all(fixtures_dir: Path = DEFAULT_FIXTURES_DIR) -> VerificationSummary:
    """Verify the complete committed corpus and its USSR-date requirement."""
    paths = sorted(fixtures_dir.glob("*.json"))
    if len(paths) != EXPECTED_FIXTURE_COUNT:
        raise FixtureVerificationError(
            f"expected exactly {EXPECTED_FIXTURE_COUNT} fixtures, found {len(paths)}"
        )

    ussr_fixture_count = 0
    point_count = 0
    house_count = 0
    aspect_count = 0
    for path in paths:
        fixture = _load_fixture(path)
        if fixture.get("historical_ussr") is True:
            chart_day = _parse_utc(fixture["input"]["dt_utc"]).date()
            if not USSR_FIRST_DAY <= chart_day <= USSR_LAST_DAY:
                raise FixtureVerificationError(
                    f"{path.stem}: historical_ussr=true but {chart_day} is outside USSR dates"
                )
            ussr_fixture_count += 1

        points, houses, aspects = verify_fixture(path)
        point_count += points
        house_count += houses
        aspect_count += aspects

    if ussr_fixture_count < MIN_USSR_FIXTURE_COUNT:
        raise FixtureVerificationError(
            f"need at least {MIN_USSR_FIXTURE_COUNT} historical USSR fixtures, "
            f"found {ussr_fixture_count}"
        )

    return VerificationSummary(
        fixture_count=len(paths),
        ussr_fixture_count=ussr_fixture_count,
        point_count=point_count,
        house_count=house_count,
        aspect_count=aspect_count,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=DEFAULT_FIXTURES_DIR,
        help="fixture directory (default: tests/fixtures)",
    )
    args = parser.parse_args()

    try:
        summary = verify_all(args.fixtures_dir.resolve())
    except FixtureVerificationError as error:
        parser.exit(1, f"fixture verification failed: {error}\n")

    print(
        "Swiss Ephemeris direct verification passed: "
        f"{summary.fixture_count} fixtures "
        f"({summary.ussr_fixture_count} historical USSR), "
        f"{summary.point_count} points, {summary.house_count} house cusps, "
        f"{summary.aspect_count} major aspects"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
