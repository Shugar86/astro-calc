# astro-calc

**Birth data in → structured astrological facts + SVG wheel out.**

A small, stateless HTTP microservice for ephemeris calculations, built on
[kerykeion](https://github.com/g-battaglia/kerykeion) and the Swiss Ephemeris.
Give it a UTC birth instant plus coordinates; get back planetary positions,
house cusps, angles, aspects, elemental/modal distributions, and a themable SVG
chart wheel — as clean JSON.

The service is a pure function of its inputs: no geocoding, no timezone
guessing, no database, no state. Coordinate resolution and local→UTC conversion
belong to the caller.

## Why AGPL-3.0

kerykeion and the Swiss Ephemeris are AGPL-licensed. This service is published
under the **GNU AGPL-3.0** so those obligations are met cleanly: it is a
self-contained network service whose source is public. See [LICENSE](LICENSE).

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Quickstart

```bash
uv sync --extra dev
uv run uvicorn app.main:app --port 8001 --reload
```

```bash
curl -s http://localhost:8001/health | jq
```

## API

### `GET /health`

```json
{ "status": "ok", "versions": { "kerykeion": "5.x", "sweph": "2.10.03" }, "calc_version": "1.0.1" }
```

### `POST /v1/natal`

Request:

```json
{
  "name": "Elena",
  "dt_utc": "1988-03-14T09:30:00Z",
  "lat": 55.7887, "lng": 49.1221, "tz": "Europe/Moscow",
  "house_system": "placidus", "zodiac": "tropical",
  "with_svg": true, "svg_variant": "wheel",
  "houses_mode": "full"
}
```

`dt_utc` must include an explicit UTC offset (`Z` is preferred), and `tz` must
be a valid IANA timezone identifier. Naive datetimes and unknown timezones are
rejected with HTTP 422.

Response (abridged):

```json
{
  "points": [
    {"id": "sun", "sign": "pisces", "sign_deg": 24.02, "abs_deg": 354.02,
     "house": 9, "retrograde": false, "speed": 0.997}
  ],
  "houses": [{"n": 1, "sign": "leo", "cusp_abs_deg": 122.95}],
  "angles": {"asc": {"sign": "leo", "sign_deg": 2.95, "abs_deg": 122.95}, "mc": {"...": "..."}},
  "aspects": [{"a": "sun", "b": "north_node", "type": "conjunction", "orb": 0.74, "applying": false}],
  "distributions": {"elements": {"fire": 0, "earth": 6, "air": 2, "water": 2},
                    "qualities": {"cardinal": 4, "fixed": 5, "mutable": 1}},
  "svg": "<svg ...>",
  "meta": {"house_system": "placidus", "zodiac": "tropical",
           "engine": "kerykeion 5.x", "calc_version": "1.0.1", "time_unknown": false}
}
```

Points computed: Sun–Pluto, Chiron, Mean Lilith, Mean North Node. Aspects are
**major only** (conjunction, opposition, trine, square, sextile). Distributions
are integer counts over the 10 classical planets. ASC and MC use kerykeion's
explicit `Ascendant` / `Medium_Coeli` points, so they stay independent of the
selected house system.

**Unknown birth time.** Set `"houses_mode": "noon_no_houses"`: the chart is
computed for 12:00 local on the birth date, houses / ASC / MC and per-point
house assignments are omitted, and `meta.time_unknown` is `true`.

### `POST /v1/synastry`

Scaffold: two subjects → cross-chart major aspects, in the shape kerykeion
provides out of the box. Not a polished product surface.

## SVG theming

The wheel SVG colors are CSS custom properties (`var(--kerykeion-chart-color-*)`),
so a consumer recolors a chart by overriding those variables in its own
stylesheet — no SVG string surgery required. kerykeion's built-in themes are a
fixed set (`light`, `dark`, `classic`, `strawberry`, …); the service renders a
neutral default and leaves palette customization to the caller. `svg_variant`
is `wheel` (wheel only) or `full` (wheel + aspect grid). Subject names are XML-
escaped before rendering so the returned markup remains safe and well-formed.

## Golden tests

`tests/fixtures/*.json` contain five reference charts calculated directly with
the `pyswisseph` API, without calling `app.engine` or Kerykeion calculation
code. Three fixtures are historical USSR dates (the acceptance minimum is two).
They cover all 13 public points, 12 Placidus cusps and the complete major-aspect
list. Tolerances are 0.01° for point longitudes and 0.05° for house cusps; the
aspect keys must match exactly.

Verify the committed corpus against Swiss Ephemeris:

```bash
uv run python scripts/verify_fixtures.py
```

Regenerate and then verify it:

```bash
uv run python scripts/gen_fixtures.py
uv run python scripts/verify_fixtures.py
```

The metadata flag is deliberately named
`verified_against_swiss_ephemeris_direct`; these fixtures have **not** been
claimed as manual astro.com UI comparisons. See
[Golden-fixture verification](docs/golden-fixtures.md) for the exact oracle,
flags, bodies, aspect orbs and limitations.

### Stage 1 definition of done

- [x] Stateless `/health`, `/v1/natal` and `/v1/synastry` HTTP contracts.
- [x] Tropical and sidereal calculation, seven house systems, unknown-time
  mode, structured points/houses/angles/aspects/distributions and safe SVG.
- [x] Five golden charts verified through direct Swiss Ephemeris calls,
  including three historical USSR dates.
- [x] Independent oracle and service regression both run under pytest; CI also
  invokes the five-fixture verifier explicitly.
- [x] Frozen dependency lock, lint, tests and container build instructions.

## Tests & lint

```bash
uv lock --check
uv run python scripts/verify_fixtures.py
uv run pytest -q
uv run ruff check .
```

## Docker

```bash
docker build -t astro-calc .
docker run --rm -p 8001:8000 astro-calc
```

## License

[GNU AGPL-3.0-or-later](LICENSE).
