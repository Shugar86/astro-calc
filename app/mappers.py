"""Pure transforms from kerykeion models to astro-calc's stable contract.

Kept side-effect free so they are trivial to unit-test and reason about.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from .config import (
    CLASSICAL_PLANETS,
    HOUSE_FIELDS,
    HOUSE_NUM,
    POINT_ID,
    SIGN_BY_NUM,
)
from .schemas import Angle, Aspect, Distributions, HouseCusp, Point

_ELEMENTS = {"fire", "earth", "air", "water"}
_QUALITIES = {"cardinal", "fixed", "mutable"}


def _sign_name(point: dict[str, Any]) -> str:
    """Full lowercase sign name from a kerykeion point's ``sign_num``."""
    return SIGN_BY_NUM[point["sign_num"]]


def map_point(kery_name: str, point: dict[str, Any], *, include_house: bool) -> Point:
    """Map one kerykeion celestial point to a contract ``Point``.

    Args:
        kery_name: kerykeion point name (e.g. ``"Sun"``).
        point: ``model_dump()`` of the point.
        include_house: Whether to emit the house number (False when time unknown).
    """
    house = HOUSE_NUM.get(point.get("house")) if include_house else None
    return Point(
        id=POINT_ID[kery_name],
        sign=_sign_name(point),
        sign_deg=round(point["position"], 4),
        abs_deg=round(point["abs_pos"], 4),
        house=house,
        retrograde=bool(point["retrograde"]),
        speed=round(point["speed"], 4),
    )


def map_houses(subject: dict[str, Any]) -> list[HouseCusp]:
    """Map the 12 house cusps in order (cusp 1..12)."""
    cusps: list[HouseCusp] = []
    for n, field in enumerate(HOUSE_FIELDS, start=1):
        cusp = subject[field]
        cusps.append(
            HouseCusp(n=n, sign=_sign_name(cusp), cusp_abs_deg=round(cusp["abs_pos"], 4))
        )
    return cusps


def _angle(cusp: dict[str, Any]) -> Angle:
    return Angle(
        sign=_sign_name(cusp),
        sign_deg=round(cusp["position"], 4),
        abs_deg=round(cusp["abs_pos"], 4),
    )


def map_angles(subject: dict[str, Any]) -> dict[str, Angle]:
    """ASC = 1st house cusp, MC = 10th house cusp (quadrant house systems)."""
    return {
        "asc": _angle(subject["first_house"]),
        "mc": _angle(subject["tenth_house"]),
    }


def map_aspects(raw_aspects: list[dict[str, Any]]) -> list[Aspect]:
    """Map chart-data aspects to the contract, keeping only known points."""
    out: list[Aspect] = []
    for asp in raw_aspects:
        a = POINT_ID.get(asp["p1_name"])
        b = POINT_ID.get(asp["p2_name"])
        if a is None or b is None:
            continue  # angle/other participants are out of contract scope
        out.append(
            Aspect(
                a=a,
                b=b,
                type=asp["aspect"],
                orb=round(asp["orbit"], 2),
                applying=asp.get("aspect_movement") == "Applying",
            )
        )
    return out


def compute_distributions(subject: dict[str, Any]) -> Distributions:
    """Integer element/quality counts over the 10 classical planets (spec §4.2)."""
    elements: Counter[str] = Counter()
    qualities: Counter[str] = Counter()
    for name in CLASSICAL_PLANETS:
        pt = subject[name.lower()]
        elements[pt["element"].lower()] += 1
        qualities[pt["quality"].lower()] += 1
    return Distributions(
        elements={e: elements.get(e, 0) for e in ("fire", "earth", "air", "water")},
        qualities={q: qualities.get(q, 0) for q in ("cardinal", "fixed", "mutable")},
    )
