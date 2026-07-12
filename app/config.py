"""Static constants and version metadata for astro-calc.

`CALC_VERSION` is bumped on ANY change that affects the numbers returned by the
service, so downstream consumers can invalidate caches and detect drift.
"""

from __future__ import annotations

import importlib.metadata

# Bump on any change that affects returned numbers (positions, houses, angles, aspects).
CALC_VERSION = "1.0.1"

# Celestial points we compute, in a stable output order.
# Sun–Pluto + Chiron + Mean Lilith + Mean North Node (per spec §4.2).
ACTIVE_POINTS: list[str] = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "Chiron", "Mean_Lilith",
    "Mean_North_Lunar_Node",
]

# Angles calculated on the subject model, but excluded from public ``points``
# and from aspect calculation.
ANGLE_POINTS: list[str] = ["Ascendant", "Medium_Coeli"]

# The 10 classical planets used for element / quality distributions.
CLASSICAL_PLANETS: list[str] = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto",
]

# Major aspects only (name, orb), per spec — minor aspects are out of scope.
MAJOR_ASPECTS: list[dict[str, object]] = [
    {"name": "conjunction", "orb": 10},
    {"name": "opposition", "orb": 10},
    {"name": "trine", "orb": 8},
    {"name": "square", "orb": 5},
    {"name": "sextile", "orb": 6},
]

# kerykeion celestial-point name -> our stable output id.
POINT_ID: dict[str, str] = {
    "Sun": "sun", "Moon": "moon", "Mercury": "mercury", "Venus": "venus",
    "Mars": "mars", "Jupiter": "jupiter", "Saturn": "saturn", "Uranus": "uranus",
    "Neptune": "neptune", "Pluto": "pluto", "Chiron": "chiron",
    "Mean_Lilith": "lilith", "Mean_North_Lunar_Node": "north_node",
}

# sign_num (0-based from Aries) -> full lowercase english name.
SIGN_BY_NUM: list[str] = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

# kerykeion house name -> 1-based number.
HOUSE_NUM: dict[str, int] = {
    "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
    "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
    "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12,
}

# Ordered house field names on the subject model (cusp 1..12).
HOUSE_FIELDS: list[str] = [
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
]

# Public house-system name -> kerykeion single-letter identifier.
HOUSE_SYSTEMS: dict[str, str] = {
    "placidus": "P", "koch": "K", "whole_sign": "W", "equal": "A",
    "regiomontanus": "R", "campanus": "C", "porphyry": "O",
}

ZODIAC_TYPES: dict[str, str] = {"tropical": "Tropical", "sidereal": "Sidereal"}


def engine_versions() -> dict[str, str]:
    """Return the versions that determine the numbers (for /health and meta).

    Returns:
        Mapping with ``kerykeion``, ``sweph`` and ``calc_version`` strings.
    """
    try:
        import swisseph as swe

        sweph = str(swe.version)
    except Exception:  # pragma: no cover - swisseph always ships with kerykeion
        sweph = "unknown"
    return {
        "kerykeion": importlib.metadata.version("kerykeion"),
        "sweph": sweph,
        "calc_version": CALC_VERSION,
    }
