import datetime as dt

from dateutil.relativedelta import relativedelta

_STEP_BY_FREQUENCY: dict[str, relativedelta] = {
    "WEEKLY": relativedelta(weeks=1),
    "BIWEEKLY": relativedelta(weeks=2),
    "MONTHLY": relativedelta(months=1),
    "QUARTERLY": relativedelta(months=3),
    "SEMIANNUAL": relativedelta(months=6),
    "ANNUAL": relativedelta(years=1),
}


class UnknownFrequencyError(ValueError):
    pass


def next_occurrence_after(current: dt.date, frequency: str) -> dt.date:
    step = _STEP_BY_FREQUENCY.get(frequency)
    if step is None:
        raise UnknownFrequencyError(frequency)
    return current + step


def occurrences_between(
    start_date: dt.date, frequency: str, range_start: dt.date, range_end: dt.date, end_date: dt.date | None = None
) -> list[dt.date]:
    """All occurrence dates within [range_start, range_end], honoring the rule's own end_date."""
    if frequency not in _STEP_BY_FREQUENCY:
        raise UnknownFrequencyError(frequency)

    occurrences: list[dt.date] = []
    current = start_date
    while current < range_start:
        current = next_occurrence_after(current, frequency)

    while current <= range_end and (end_date is None or current <= end_date):
        occurrences.append(current)
        current = next_occurrence_after(current, frequency)

    return occurrences
