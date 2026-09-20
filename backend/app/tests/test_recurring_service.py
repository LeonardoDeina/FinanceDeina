import datetime as dt

import pytest

from app.recurring.service import UnknownFrequencyError, next_occurrence_after, occurrences_between


def test_monthly_next_occurrence_handles_month_end_correctly():
    # Jan 31 + 1 month -> Feb 28 (dateutil clamps), not Mar 3
    assert next_occurrence_after(dt.date(2026, 1, 31), "MONTHLY") == dt.date(2026, 2, 28)


def test_weekly_occurrences_within_range():
    occurrences = occurrences_between(
        start_date=dt.date(2026, 1, 5),
        frequency="WEEKLY",
        range_start=dt.date(2026, 1, 1),
        range_end=dt.date(2026, 1, 31),
    )
    assert occurrences == [dt.date(2026, 1, 5), dt.date(2026, 1, 12), dt.date(2026, 1, 19), dt.date(2026, 1, 26)]


def test_occurrences_respect_rule_end_date():
    occurrences = occurrences_between(
        start_date=dt.date(2026, 1, 1),
        frequency="MONTHLY",
        range_start=dt.date(2026, 1, 1),
        range_end=dt.date(2026, 6, 30),
        end_date=dt.date(2026, 3, 1),
    )
    assert occurrences == [dt.date(2026, 1, 1), dt.date(2026, 2, 1), dt.date(2026, 3, 1)]


def test_occurrences_skip_dates_before_range_start():
    occurrences = occurrences_between(
        start_date=dt.date(2025, 1, 1),
        frequency="MONTHLY",
        range_start=dt.date(2026, 1, 1),
        range_end=dt.date(2026, 2, 28),
    )
    assert occurrences == [dt.date(2026, 1, 1), dt.date(2026, 2, 1)]


def test_unknown_frequency_raises():
    with pytest.raises(UnknownFrequencyError):
        next_occurrence_after(dt.date(2026, 1, 1), "DAILY")
