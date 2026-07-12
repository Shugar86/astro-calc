"""Pydantic request/response contracts for the astro-calc API (spec §4.1-4.2)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator

HouseSystem = Literal[
    "placidus", "koch", "whole_sign", "equal", "regiomontanus", "campanus", "porphyry"
]
Zodiac = Literal["tropical", "sidereal"]
HousesMode = Literal["full", "noon_no_houses"]
SvgVariant = Literal["wheel", "full"]


class SubjectIn(BaseModel):
    """Birth data for a single subject (already resolved to UTC + coordinates).

    The caller (arcana) owns geocoding and local->UTC conversion; astro-calc is a
    pure function of coordinates + UTC instant.
    """

    name: str = "Subject"
    dt_utc: datetime = Field(..., description="Birth instant in UTC (ISO-8601, e.g. 1988-03-14T09:30:00Z)")
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    tz: str = Field(..., description="IANA timezone, e.g. Europe/Moscow")
    house_system: HouseSystem = "placidus"
    zodiac: Zodiac = "tropical"
    houses_mode: HousesMode = "full"

    @field_validator("dt_utc")
    @classmethod
    def require_timezone_aware_datetime(cls, value: datetime) -> datetime:
        """Reject ambiguous instants without an explicit UTC offset."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("dt_utc must include a UTC offset (for example, Z or +03:00)")
        return value

    @field_validator("tz")
    @classmethod
    def require_iana_timezone(cls, value: str) -> str:
        """Reject timezone identifiers that cannot be resolved by IANA tzdata."""
        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError) as exc:
            raise ValueError("tz must be a valid IANA timezone") from exc
        return value


class NatalRequest(SubjectIn):
    """Request body for ``POST /v1/natal``."""

    with_svg: bool = False
    svg_variant: SvgVariant = "wheel"


class SynastryRequest(BaseModel):
    """Request body for ``POST /v1/synastry`` (scaffold — not a product surface)."""

    first: SubjectIn
    second: SubjectIn


# --- Response models ---------------------------------------------------------


class Point(BaseModel):
    """A celestial point placement."""

    id: str
    sign: str
    sign_deg: float = Field(..., description="Degrees within the sign (0-30)")
    abs_deg: float = Field(..., description="Absolute ecliptic longitude (0-360)")
    house: int | None = Field(None, description="House 1-12; null when time is unknown")
    retrograde: bool
    speed: float


class HouseCusp(BaseModel):
    n: int
    sign: str
    cusp_abs_deg: float


class Angle(BaseModel):
    sign: str
    sign_deg: float
    abs_deg: float


class Aspect(BaseModel):
    a: str
    b: str
    type: str
    orb: float
    applying: bool


class Distributions(BaseModel):
    elements: dict[str, int]
    qualities: dict[str, int]


class Meta(BaseModel):
    house_system: str
    zodiac: str
    engine: str
    calc_version: str
    time_unknown: bool


class NatalResponse(BaseModel):
    points: list[Point]
    houses: list[HouseCusp] | None = None
    angles: dict[str, Angle] | None = None
    aspects: list[Aspect]
    distributions: Distributions
    svg: str | None = None
    meta: Meta


class SynastryResponse(BaseModel):
    aspects: list[Aspect]
    meta: Meta


class Health(BaseModel):
    status: str
    versions: dict[str, str]
    calc_version: str
