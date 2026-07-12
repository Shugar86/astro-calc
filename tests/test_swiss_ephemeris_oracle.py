"""Acceptance test for the direct pyswisseph fixture oracle."""

from scripts.verify_fixtures import verify_all


def test_all_golden_fixtures_match_direct_swiss_ephemeris() -> None:
    summary = verify_all()

    assert summary.fixture_count == 5
    assert summary.ussr_fixture_count >= 2
    assert summary.point_count == 5 * 13
    assert summary.house_count == 5 * 12
    assert summary.aspect_count > 0
