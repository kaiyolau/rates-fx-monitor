from datetime import date

import pytest

from pipeline.analytics import run_quality_checks
from tests.conftest import LAST_DAY, clean_rows


def statuses(con, as_of=LAST_DAY):
    return {c["check_name"]: c["status"] for c in run_quality_checks(con, as_of)}


def check(con, name, as_of=LAST_DAY):
    return next(c for c in run_quality_checks(con, as_of) if c["check_name"] == name)


def test_clean_data_passes_every_check(db):
    assert set(statuses(db(clean_rows())).values()) == {"pass"}


def test_duplicate_date_fails(db):
    rows = clean_rows() + [("FXUSDCAD", date(2026, 1, 15), 1.4)]
    result = check(db(rows), "Duplicate dates")
    assert result["status"] == "fail"
    assert "FXUSDCAD on 2026-01-15" in result["message"]


def test_null_value_warns(db):
    rows = [r if r[:2] != ("FXEURCAD", date(2026, 1, 15)) else ("FXEURCAD", r[1], None) for r in clean_rows()]
    result = check(db(rows), "Null values")
    assert result["status"] == "warn"
    assert "FXEURCAD (1)" in result["message"]


@pytest.mark.parametrize("as_of, expected", [
    (date(2026, 2, 2), "pass"),   # Monday after a Friday observation: 1 business day
    (date(2026, 2, 4), "warn"),   # Wednesday: 3 business days
    (date(2026, 2, 9), "fail"),   # next Monday: 6 business days
])
def test_stale_data_counts_business_days_not_weekends(db, as_of, expected):
    assert check(db(clean_rows()), "Stale data", as_of)["status"] == expected


def test_missing_day_for_one_series_warns(db):
    rows = [r for r in clean_rows() if r[:2] != ("BD.CDN.5YR.DQ.YLD", date(2026, 1, 14))]
    result = check(db(rows), "Missing business days")
    assert result["status"] == "warn"
    assert "BD.CDN.5YR.DQ.YLD (1)" in result["message"]


def test_holiday_reported_only_by_policy_rate_is_not_a_gap(db):
    # Real case: V39079 is published on statutory holidays while markets are closed.
    holiday = date(2026, 1, 19)
    rows = [r for r in clean_rows() if r[1] != holiday or r[0] == "V39079"]
    result = check(db(rows), "Missing business days")
    assert result["status"] == "pass"
    assert "1 weekday(s) treated as holidays" in result["message"]


def test_partial_outage_is_a_gap_not_a_holiday(db):
    # Found by the /review checklist: 5 of 8 series missing must not look like a holiday.
    outage = {"BD.CDN.2YR.DQ.YLD", "BD.CDN.5YR.DQ.YLD", "BD.CDN.10YR.DQ.YLD", "AVG.INTWO", "FXUSDCAD"}
    rows = [r for r in clean_rows() if not (r[1] == date(2026, 1, 14) and r[0] in outage)]
    result = check(db(rows), "Missing business days")
    assert result["status"] == "warn"
    assert "0 weekday(s) treated as holidays" in result["message"]


def test_large_daily_jump_warns(db):
    rows = [r if r[:2] != ("FXGBPCAD", date(2026, 1, 20)) else ("FXGBPCAD", r[1], 1.9) for r in clean_rows()]
    result = check(db(rows), "Outliers (large daily jumps)")
    assert result["status"] == "warn"  # 1.80 -> 1.90 is +5.6%
    assert "FXGBPCAD on 2026-01-20" in result["message"]
