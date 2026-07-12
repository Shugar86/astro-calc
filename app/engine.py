"""Orchestration: birth data -> kerykeion -> structured facts (+ optional SVG)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.schemas.kr_models import AstrologicalSubjectModel

from .config import (
    ACTIVE_POINTS,
    HOUSE_SYSTEMS,
    MAJOR_ASPECTS,
    ZODIAC_TYPES,
    engine_versions,
)
from .mappers import (
    compute_distributions,
    map_angles,
    map_aspects,
    map_houses,
    map_point,
)
from .schemas import (
    Meta,
    NatalRequest,
    NatalResponse,
    SubjectIn,
    SynastryRequest,
    SynastryResponse,
)
from .svg import render_svg

_KERYKEION_VERSION = engine_versions()["kerykeion"]


def _iso_utc(dt_utc: datetime, tz: str, *, noon: bool) -> str:
    """Return the effective birth instant as ``YYYY-MM-DDThh:mm:ssZ``.

    In ``noon`` mode (birth time unknown) the clock time is discarded and the
    chart is computed for 12:00 local on the birth date — the standard
    convention that keeps fast-moving points near their mid-day best guess.
    A naive ``dt_utc`` is interpreted as UTC.
    """
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    dt_utc = dt_utc.astimezone(timezone.utc)
    if noon:
        local_noon = dt_utc.astimezone(ZoneInfo(tz)).replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        dt_utc = local_noon.astimezone(timezone.utc)
    return dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_subject(subj: SubjectIn) -> AstrologicalSubjectModel:
    """Compute and return the kerykeion subject model for the given birth data."""
    time_unknown = subj.houses_mode == "noon_no_houses"
    return AstrologicalSubjectFactory.from_iso_utc_time(
        name=subj.name,
        iso_utc_time=_iso_utc(subj.dt_utc, subj.tz, noon=time_unknown),
        lng=subj.lng,
        lat=subj.lat,
        tz_str=subj.tz,
        city="Natal",
        nation="XX",
        online=False,
        houses_system_identifier=HOUSE_SYSTEMS[subj.house_system],
        zodiac_type=ZODIAC_TYPES[subj.zodiac],
        active_points=ACTIVE_POINTS,
    )


def _meta(subj: SubjectIn, *, time_unknown: bool) -> Meta:
    return Meta(
        house_system=subj.house_system,
        zodiac=subj.zodiac,
        engine=f"kerykeion {_KERYKEION_VERSION}",
        calc_version=engine_versions()["calc_version"],
        time_unknown=time_unknown,
    )


def build_natal(req: NatalRequest) -> NatalResponse:
    """Build the full natal-chart facts payload for a request."""
    time_unknown = req.houses_mode == "noon_no_houses"
    model = _build_subject(req)
    dump = model.model_dump()

    chart_data = ChartDataFactory.create_natal_chart_data(
        model,
        active_points=ACTIVE_POINTS,
        active_aspects=MAJOR_ASPECTS,
    )
    aspects = map_aspects(chart_data.model_dump()["aspects"])

    points = [
        map_point(name, dump[name.lower()], include_house=not time_unknown)
        for name in ACTIVE_POINTS
    ]

    svg = render_svg(chart_data, req.svg_variant) if req.with_svg else None

    return NatalResponse(
        points=points,
        houses=None if time_unknown else map_houses(dump),
        angles=None if time_unknown else map_angles(dump),
        aspects=aspects,
        distributions=compute_distributions(dump),
        svg=svg,
        meta=_meta(req, time_unknown=time_unknown),
    )


def build_synastry(req: SynastryRequest) -> SynastryResponse:
    """Cross-chart aspects between two subjects (scaffold, spec §4.1)."""
    first = _build_subject(req.first)
    second = _build_subject(req.second)
    chart_data = ChartDataFactory.create_synastry_chart_data(
        first, second, active_points=ACTIVE_POINTS, active_aspects=MAJOR_ASPECTS
    )
    aspects = map_aspects(chart_data.model_dump()["aspects"])
    return SynastryResponse(aspects=aspects, meta=_meta(req.first, time_unknown=False))
