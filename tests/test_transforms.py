from datetime import date

import pytest

from pipeline.analytics import compute_metrics

Y2, Y5, Y10 = "BD.CDN.2YR.DQ.YLD", "BD.CDN.5YR.DQ.YLD", "BD.CDN.10YR.DQ.YLD"


def by_series(result):
    return {m["series"]: m for m in result["metrics"]}


def test_one_day_change_skips_the_weekend(db):
    rows = [(Y2, date(2026, 1, 23), 3.00), (Y2, date(2026, 1, 26), 3.05)]  # Fri, Mon
    m = by_series(compute_metrics(db(rows)))[Y2]
    assert m["latest_date"] == date(2026, 1, 26)
    assert m["latest_value"] == 3.05
    assert m["prev_date"] == date(2026, 1, 23)
    assert m["change_1d"] == pytest.approx(0.05)


def test_month_and_year_changes_use_last_observation_on_or_before_target(db):
    rows = [
        (Y2, date(2025, 1, 24), 2.50),   # year target 2025-01-26 is a Sunday -> use Friday
        (Y2, date(2025, 12, 24), 2.90),  # month target 2025-12-26 has no data -> use 12-24
        (Y2, date(2026, 1, 26), 3.00),
    ]
    m = by_series(compute_metrics(db(rows)))[Y2]
    assert m["change_1m"] == pytest.approx(0.10)
    assert m["change_1y"] == pytest.approx(0.50)


def test_spread_is_10y_minus_2y_on_common_dates_only(db):
    rows = [
        (Y2, date(2026, 1, 22), 3.00), (Y10, date(2026, 1, 22), 3.40),
        (Y2, date(2026, 1, 23), 3.10), (Y10, date(2026, 1, 23), 3.45),
        (Y10, date(2026, 1, 26), 3.60),  # no 2Y value that day -> no spread
    ]
    result = compute_metrics(db(rows))
    assert [(r["date"], r["spread"]) for r in result["spread_history"]] == [
        (date(2026, 1, 22), pytest.approx(0.40)),
        (date(2026, 1, 23), pytest.approx(0.35)),
    ]
    spread = by_series(result)["SPREAD_10Y_2Y"]
    assert spread["latest_value"] == pytest.approx(0.35)
    assert spread["change_1d"] == pytest.approx(-0.05)


def test_yield_curve_snapshot_today_month_ago_year_ago(db):
    rows = []
    for sid, base in [(Y2, 3.0), (Y5, 3.2), (Y10, 3.5)]:
        rows += [(sid, date(2025, 1, 30), base - 0.5),
                 (sid, date(2025, 12, 30), base - 0.1),
                 (sid, date(2026, 1, 30), base)]
    curve = compute_metrics(db(rows))["yield_curve"]
    assert [c["tenor"] for c in curve] == ["2Y", "5Y", "10Y"]
    ten = curve[2]
    assert (ten["today"], ten["month_ago"], ten["year_ago"]) == (3.5, pytest.approx(3.4), 3.0)


def test_percent_change_is_null_when_previous_value_is_zero(db):
    rows = [("FXUSDCAD", date(2026, 1, 29), 0.0), ("FXUSDCAD", date(2026, 1, 30), 1.4)]
    m = by_series(compute_metrics(db(rows)))["FXUSDCAD"]
    assert m["change_1d"] == pytest.approx(1.4)
    assert m["pct_change_1d"] is None
