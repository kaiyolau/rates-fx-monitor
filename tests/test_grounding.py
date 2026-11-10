"""Tiny evaluation of the AI-summary grounding check."""

from pipeline import summary
from pipeline.series import SERIES, SPREAD_ROW

KINDS = {s[0]: s[2] for s in SERIES + [SPREAD_ROW]}
LABELS = {s[0]: s[1] for s in SERIES + [SPREAD_ROW]}


def metric(series, latest, d1, m1=None, y1=None, pct=None):
    return {"series": series, "latest_value": latest, "change_1d": d1, "change_1m": m1,
            "change_1y": y1, "pct_change_1d": pct, "pct_change_1m": None, "pct_change_1y": None}


METRICS = [
    metric("V39079", 2.50, 0.0, 0.0, -0.25),
    metric("BD.CDN.2YR.DQ.YLD", 3.13, 0.01),
    metric("BD.CDN.10YR.DQ.YLD", 3.63, -0.02),
    metric("SPREAD_10Y_2Y", 0.50, -0.03),
    metric("FXUSDCAD", 1.4123, 0.0010, pct=0.0709),
]
ALLOWED = summary.allowed_numbers(METRICS, KINDS)


def test_summary_with_made_up_number_is_rejected():
    text = "The 10Y yield fell 2 bps to 3.63%, while the policy rate was cut to 2.25%."
    result = summary.grounding_check(text, ALLOWED)
    assert not result["passed"]
    assert result["unverified"] == ["2.25"]


def test_correct_summary_passes():
    text = ("The 2Y yield rose 1 bp to 3.13% and the 10Y yield fell 2 bps to 3.63%, "
            "so the 10Y-2Y spread narrowed 3 bps to 0.50 percentage points. "
            "USD/CAD rose 0.07% to 1.4123.")
    result = summary.grounding_check(text, ALLOWED)
    assert result["passed"]
    assert result["numbers_checked"] == result["numbers_verified"] == 8


def test_rounding_is_accepted_only_when_correct():
    assert summary.grounding_check("USD/CAD was about 1.41.", ALLOWED)["passed"]       # 1.4123 -> 1.41
    assert summary.grounding_check("The 10Y yield is 3.6%.", ALLOWED)["passed"]        # 3.63 -> 3.6
    assert not summary.grounding_check("The 10Y yield is 3.7%.", ALLOWED)["passed"]    # wrong rounding
    assert not summary.grounding_check("USD/CAD was about 1.42.", ALLOWED)["passed"]


def test_rejected_ai_text_falls_back_to_verified_template(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(summary, "llm_summary", lambda m, l: "The 2Y yield jumped 40 bps to 3.53%.")
    result = summary.build_summary(METRICS, LABELS, KINDS)
    assert result["source"] == "rule_based"
    assert result["ai_status"] == "rejected"
    assert result["numbers_checked"] == result["numbers_verified"] > 0

    monkeypatch.setattr(summary, "llm_summary", lambda m, l: "The 10Y yield fell 2 bps to 3.63%.")
    result = summary.build_summary(METRICS, LABELS, KINDS)
    assert result["source"] == "ai"
    assert (result["numbers_checked"], result["numbers_verified"]) == (2, 2)
