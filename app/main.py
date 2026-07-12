"""astro-calc — stateless ephemeris microservice.

Birth data in -> structured astrological facts + SVG wheel out.
Built on kerykeion / Swiss Ephemeris. See README for the API contract.
"""

from __future__ import annotations

from fastapi import FastAPI

from .config import engine_versions
from .engine import build_natal, build_synastry
from .schemas import (
    Health,
    NatalRequest,
    NatalResponse,
    SynastryRequest,
    SynastryResponse,
)

app = FastAPI(
    title="astro-calc",
    version=engine_versions()["calc_version"],
    summary="Birth data in, structured astrological facts + SVG wheel out.",
)


@app.get("/health", response_model=Health)
def health() -> Health:
    """Liveness + engine versions (kerykeion / Swiss Ephemeris / calc_version)."""
    v = engine_versions()
    return Health(
        status="ok",
        versions={"kerykeion": v["kerykeion"], "sweph": v["sweph"]},
        calc_version=v["calc_version"],
    )


@app.post("/v1/natal", response_model=NatalResponse, response_model_exclude_none=True)
def natal(req: NatalRequest) -> NatalResponse:
    """Compute a natal chart: points, houses, angles, aspects, distributions, SVG."""
    return build_natal(req)


@app.post("/v1/synastry", response_model=SynastryResponse)
def synastry(req: SynastryRequest) -> SynastryResponse:
    """Cross-chart aspects between two subjects (scaffold — not polished)."""
    return build_synastry(req)
