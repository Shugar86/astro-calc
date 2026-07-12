# Golden-fixture verification

The five committed charts are verified against Swiss Ephemeris directly. The
oracle in [`scripts/verify_fixtures.py`](../scripts/verify_fixtures.py) imports
`swisseph` (the module supplied by `pyswisseph`) and deliberately does not
import `app.engine`, `app.config`, Kerykeion models or Kerykeion aspect code.
This makes the fixture calculation path independent of the service
orchestration and mapping path.

## Exact method

For every fixture the verifier:

1. Parses the offset-aware `dt_utc`, normalizes it to UTC and converts it to a
   Gregorian Julian day with `swe.julday`.
2. Calls `swe.calc_ut(jd, body, swe.FLG_SWIEPH | swe.FLG_SPEED)` for Sun,
   Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Chiron,
   mean lunar apogee (the public `lilith`) and mean north lunar node.
3. Calls `swe.houses_ex(jd, lat, lng, b"P", flags)` for the twelve Placidus
   cusps.
4. Independently computes the shortest angular separation for every pair of
   public points and applies the public major-aspect orbs: conjunction 10°,
   opposition 10°, trine 8°, square 5° and sextile 6°.
5. Compares positions modulo 360° using the fixture tolerances and requires an
   exact, order-independent match for the complete aspect-key list.

The underlying API sequence follows the official
[Swiss Ephemeris programmer's manual](https://www.astro.com/swisseph/swephprg.pdf):
set the ephemeris path, obtain a Julian day and call `swe_calc_ut`. The Python
binding and return shape can be inspected in the upstream
[`pyswisseph.c`](https://github.com/astrorigin/pyswisseph/blob/master/pyswisseph.c).

The installed Kerykeion distribution is used only to locate its bundled Swiss
Ephemeris data directory, notably `seas_18.se1` for Chiron. No Kerykeion Python
module is imported or executed by the oracle. Set `SE_EPHE_PATH` to verify with
another compatible ephemeris data directory.

## Corpus and CI invariant

The verifier fails unless the corpus contains exactly five JSON fixtures. It
also fails unless at least two are explicitly marked `historical_ussr: true`
and their UTC dates fall between 1922-12-30 and 1991-12-26. The shipped corpus
has three: Leningrad 1975, Novosibirsk 1982 and Kazan 1988.

Each fixture must contain exactly 13 point longitudes, cusps 1–12, unique
aspect keys and `verified_against_swiss_ephemeris_direct: true`. CI executes
the standalone verifier as its own step and pytest repeats it before the
service-vs-fixture regression test is considered green.

Run:

```bash
uv run python scripts/verify_fixtures.py
```

A successful run reports the chart, USSR-date, point, cusp and aspect totals.

## What this claim does and does not mean

`verified_against_swiss_ephemeris_direct: true` means that the committed values
match native `pyswisseph` calls, independently of astro-calc/Kerykeion's
calculation path. It is not a claim of manual comparison with the astro.com
website, so no `verified_against_astro_com` flag is present.

Both the service and oracle ultimately use Swiss Ephemeris. The oracle is
designed to catch service-level date conversion, body selection, house-system,
aspect-orb, mapping and dependency drift; it is not a second astronomical
ephemeris implementation capable of detecting an error inside Swiss Ephemeris
itself.
