"""Conversation list timestamps must carry an explicit UTC offset.

Regression test for the IST-midnight grouping bug: naive DB timestamps were
serialized without an offset and browsers parsed them as local time.
"""

from datetime import datetime, timezone, timedelta

from app.core.timefmt import iso_with_utc as _iso_with_utc


def test_naive_datetime_gets_utc_offset():
    assert _iso_with_utc(datetime(2026, 10, 30, 20, 0, 0)) == "2026-10-30T20:00:00+00:00"


def test_aware_datetime_keeps_its_offset():
    ist = timezone(timedelta(hours=5, minutes=30))
    assert _iso_with_utc(datetime(2026, 10, 31, 1, 30, tzinfo=ist)) == "2026-10-31T01:30:00+05:30"


def test_naive_string_gets_z_suffix():
    assert _iso_with_utc("2026-10-30T20:00:00") == "2026-10-30T20:00:00Z"


def test_offset_strings_pass_through():
    assert _iso_with_utc("2026-10-30T20:00:00Z") == "2026-10-30T20:00:00Z"
    assert _iso_with_utc("2026-10-30T20:00:00+00:00") == "2026-10-30T20:00:00+00:00"
    assert _iso_with_utc("2026-10-30T20:00:00.123456+05:30") == "2026-10-30T20:00:00.123456+05:30"


def test_none_passes_through():
    assert _iso_with_utc(None) is None


def test_ist_midnight_case_parses_to_today():
    # 1:30 AM IST Oct 31 = 20:00 UTC Oct 30; with the offset attached, JS
    # Date parsing lands on the correct instant instead of local Oct 30.
    iso = _iso_with_utc(datetime(2026, 10, 30, 20, 0, 0))
    parsed = datetime.fromisoformat(iso)
    ist = timezone(timedelta(hours=5, minutes=30))
    assert parsed.astimezone(ist).date().isoformat() == "2026-10-31"
