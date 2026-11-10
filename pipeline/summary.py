"""Plain-language summary of what moved.

If ANTHROPIC_API_KEY is set, Claude writes the summary and every number in it
must pass a grounding check against the source data. Otherwise, or if the
check fails, a rule-based template is used. The template is checked too.
"""

import json
import os
import re

MODEL = "claude-opus-5-5"

# Tenor and period labels such as "10Y", "2-year" or "1 month" are names, not data.
LABEL_PATTERN = re.compile(r"\b\d+\s*(?:Y|-?\s?(?:years?|yr|months?|days?))\b", re.IGNORECASE)
NUMBER_PATTERN = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")


# ---------------------------------------------------------------- grounding check

def allowed_numbers(metrics: list[dict], kinds: dict) -> list[float]:
    """Every number a summary may quote, as absolute values.

    Rates may be quoted in percent or basis points; FX changes in CAD or percent.
    """
    allowed = []
    for m in metrics:
        values = [m["latest_value"], m["change_1d"], m["change_1m"], m["change_1y"]]
        values = [abs(v) for v in values if v is not None]
        allowed.extend(values)
        if kinds.get(m["series"]) == "rate":
            allowed.extend(v * 100 for v in values)  # basis points
        else:
            pcts = [m["pct_change_1d"], m["pct_change_1m"], m["pct_change_1y"]]
            allowed.extend(abs(p) for p in pcts if p is not None)
    return allowed


def extract_numbers(text: str) -> list[str]:
    return NUMBER_PATTERN.findall(LABEL_PATTERN.sub(" ", text))


def is_verified(token: str, allowed: list[float]) -> bool:
    """True if the number is a correct rounding of some source value.

    "3.2" matches 3.21 (rounded to 1 decimal); "3.3" does not.
    """
    decimals = len(token.split(".")[1]) if "." in token else 0
    tolerance = 0.5 * 10 ** -decimals + 1e-9
    x = float(token)
    return any(abs(a - x) <= tolerance for a in allowed)


def grounding_check(text: str, allowed: list[float]) -> dict:
    numbers = extract_numbers(text)
    verified = [n for n in numbers if is_verified(n, allowed)]
    return {
        "passed": len(numbers) > 0 and len(verified) == len(numbers),
        "numbers_checked": len(numbers),
        "numbers_verified": len(verified),
        "unverified": [n for n in numbers if n not in verified],
    }


# ---------------------------------------------------------------- rule-based text

def _rate_move(m: dict) -> str:
    level = f"{m['latest_value']:.2f}%"
    if m["change_1d"] is None:
        return f"stood at {level}"
    bps = round(m["change_1d"] * 100)
    if bps == 0:
        return f"was unchanged at {level}"
    unit = "bp" if abs(bps) == 1 else "bps"
    return f"{'rose' if bps > 0 else 'fell'} {abs(bps)} {unit} to {level}"


def _fx_move(m: dict) -> str:
    level = f"{m['latest_value']:.4f}"
    pct = m["pct_change_1d"]
    if pct is None:
        return f"stood at {level}"
    if round(pct, 2) == 0:
        return f"was unchanged at {level}"
    return f"{'rose' if pct > 0 else 'fell'} {abs(pct):.2f}% to {level}"


def rule_based_summary(by_id: dict) -> str:
    y2, y10 = by_id["BD.CDN.2YR.DQ.YLD"], by_id["BD.CDN.10YR.DQ.YLD"]
    spread, policy, usd = by_id["SPREAD_10Y_2Y"], by_id["V39079"], by_id["FXUSDCAD"]

    sentences = [
        f"On the latest trading day the 2Y Government of Canada yield {_rate_move(y2)} "
        f"and the 10Y yield {_rate_move(y10)}, leaving the 10Y minus 2Y spread at "
        f"{spread['latest_value'] * 100:.0f} bps.",
        f"USD/CAD {_fx_move(usd)}.",
    ]
    year_change = policy["change_1y"]
    if year_change is None or round(year_change * 100) == 0:
        sentences.append(f"The Bank of Canada policy rate is {policy['latest_value']:.2f}%, unchanged from a year ago.")
    else:
        direction = "down" if year_change < 0 else "up"
        sentences.append(
            f"The Bank of Canada policy rate is {policy['latest_value']:.2f}%, "
            f"{direction} {abs(year_change) * 100:.0f} bps from a year ago."
        )
    return " ".join(sentences)


# ---------------------------------------------------------------- Claude

def _prompt_facts(metrics: list[dict], labels: dict) -> str:
    rows = {}
    for m in metrics:
        rows[labels.get(m["series"], m["series"])] = {
            k: m[k] for k in ("latest_value", "change_1d", "change_1m", "change_1y", "pct_change_1d")
        }
    return json.dumps(rows, indent=1)


def llm_summary(metrics: list[dict], labels: dict) -> str | None:
    """Ask Claude for a 2-3 sentence summary. Returns None on any problem."""
    try:
        import anthropic

        client = anthropic.Anthropic(timeout=60.0, max_retries=2)
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=4000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low"},
            system=(
                "You write short, neutral market notes for a dashboard. "
                "Use only numbers that appear in the data, rounded sensibly. "
                "Rates are in percent and their changes in percentage points: quote rate "
                "changes in basis points (1 pp = 100 bps). FX levels have 4 decimals; quote "
                "FX changes as percent from pct_change_1d. Do not include dates, "
                "forecasts, advice or any number not derived from the data. Use tenor labels "
                "like 2Y and 10Y."
            ),
            messages=[{
                "role": "user",
                "content": "Write 2 to 3 plain-language sentences on what moved on the latest "
                           "day (change_1d) in Canadian rates and FX. Reply with the sentences only.\n\n"
                           + _prompt_facts(metrics, labels),
            }],
        )
        if response.stop_reason != "end_turn":
            return None
        text = "".join(b.text for b in response.content if b.type == "text").strip()
        return text or None
    except Exception as err:  # noqa: BLE001 - any failure falls back to the template
        print(f"Claude summary unavailable: {type(err).__name__}: {err}")
        return None


def build_summary(metrics: list[dict], labels: dict, kinds: dict) -> dict:
    allowed = allowed_numbers(metrics, kinds)
    by_id = {m["series"]: m for m in metrics}

    ai_status = "not_configured"
    if os.environ.get("ANTHROPIC_API_KEY"):
        text = llm_summary(metrics, labels)
        if text is None:
            ai_status = "error"
        else:
            check = grounding_check(text, allowed)
            if check["passed"]:
                return {"text": text, "source": "ai", "model": MODEL, "ai_status": "verified",
                        "numbers_checked": check["numbers_checked"],
                        "numbers_verified": check["numbers_verified"]}
            ai_status = "rejected"
            print(f"Claude summary rejected, unverified numbers: {check['unverified']}\n{text}")

    text = rule_based_summary(by_id)
    check = grounding_check(text, allowed)
    return {"text": text, "source": "rule_based", "model": None, "ai_status": ai_status,
            "numbers_checked": check["numbers_checked"],
            "numbers_verified": check["numbers_verified"]}
