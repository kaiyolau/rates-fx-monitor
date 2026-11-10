"""Small, deterministic fixture data. No live API calls in tests."""

from datetime import date, timedelta

import pytest

from pipeline.analytics import load_db
from pipeline.series import SERIES

BASE_VALUES = {
    "V39079": 2.50, "AVG.INTWO": 2.52,
    "BD.CDN.2YR.DQ.YLD": 3.00, "BD.CDN.5YR.DQ.YLD": 3.20, "BD.CDN.10YR.DQ.YLD": 3.50,
    "FXUSDCAD": 1.4000, "FXEURCAD": 1.5000, "FXGBPCAD": 1.8000,
}

LAST_DAY = date(2026, 1, 30)  # a Friday


def weekdays(start: date, end: date):
    day = start
    while day <= end:
        if day.weekday() < 5:
            yield day
        day += timedelta(days=1)


def clean_rows(start=date(2025, 10, 1), end=LAST_DAY):
    """Every series on every weekday, constant values: passes all quality checks."""
    return [(sid, day, BASE_VALUES[sid]) for day in weekdays(start, end) for sid in BASE_VALUES]


@pytest.fixture
def db():
    """Build a DuckDB connection from a list of (series, date, value) rows."""
    return lambda rows: load_db(rows, SERIES)
