"""Offline. Unusable timezones must take the same no-time-of-day line as a missing one, never a false local time."""
from datetime import datetime, timezone as tz

import pytest

from app.services import llm_service
from app.services.llm_service import _local_time_line

MISSING_LINE = "The user's timezone is unknown. Do not mention the time of day (morning, afternoon, evening, tonight)."


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    fixed = datetime(2026, 11, 26, 8, 0, tzinfo=tz.utc)

    class FakeDT(datetime):
        @classmethod
        def now(cls, zone=None):
            return fixed.astimezone(zone) if zone else fixed.replace(tzinfo=None)

    monkeypatch.setattr(llm_service, "datetime", FakeDT)


def test_missing_zone_line_is_unchanged():
    for ident in ({}, {"timezone": None}, {"timezone": ""}, {"tz": None}):
        assert _local_time_line(ident) == MISSING_LINE


@pytest.mark.parametrize("bad", ["Not/AZone", "UTC+5", "../etc/passwd", "  ", "\t\n", 5, 0.5, True, ["Asia/Kolkata"], {"z": 1}, b"Asia/Kolkata"])
def test_malformed_zone_takes_exactly_the_missing_line(bad):
    assert _local_time_line({"timezone": bad}) == MISSING_LINE
    assert _local_time_line({"tz": bad}) == MISSING_LINE


def test_known_zone_wording_is_unchanged():
    assert _local_time_line({"timezone": "Asia/Kolkata"}) == (
        "The user's local time is Thursday 01:30 PM (Asia/Kolkata). "
        "Only say morning, afternoon, tonight or similar when it matches this time."
    )


def test_alias_key_and_padded_zone_work():
    assert "(Asia/Kolkata)" in _local_time_line({"tz": "Asia/Kolkata"})
    assert _local_time_line({"timezone": "  Asia/Kolkata\n"}) == _local_time_line({"timezone": "Asia/Kolkata"})


def test_literal_utc_is_a_real_zone():
    assert "local time is Thursday 08:00 AM (UTC)" in _local_time_line({"timezone": "UTC"})


def test_no_date_injection_or_new_rules():
    for ident in ({}, {"timezone": "Asia/Kolkata"}, {"timezone": "bad"}):
        line = _local_time_line(ident)
        assert "2026" not in line and "November" not in line and "recorded or mentioned" not in line
