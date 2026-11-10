"""Fetch Bank of Canada data, transform it in DuckDB and write web/public/data.json.

Usage: python -m pipeline.run
"""

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from pipeline.analytics import compute_metrics, load_db, run_quality_checks
from pipeline.series import CARD_IDS, SERIES, SERIES_IDS, SPREAD_ROW
from pipeline.summary import build_summary
from pipeline.valet import BASE_URL, fetch_observations, parse_observations

OUTPUT = Path(__file__).resolve().parent.parent / "web" / "public" / "data.json"
HISTORY_DAYS = 400  # enough for 1-year comparisons plus a margin for holidays


def to_json(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Cannot serialize {type(value)}")


def build_payload(rows, as_of: date) -> dict:
    con = load_db(rows)
    results = compute_metrics(con)
    quality = run_quality_checks(con, as_of)

    meta = {s[0]: s for s in SERIES + [SPREAD_ROW]}
    labels = {sid: m[1] for sid, m in meta.items()}
    kinds = {sid: m[2] for sid, m in meta.items()}
    metrics = [{**m, "label": labels[m["series"]], "kind": kinds[m["series"]]} for m in results["metrics"]]
    by_id = {m["series"]: m for m in metrics}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(),
        "source": {
            "name": "Bank of Canada Valet API",
            "url": BASE_URL,
            "terms_url": "https://www.bankofcanada.ca/terms/",
        },
        "cards": [by_id[sid] for sid in CARD_IDS if sid in by_id],
        "metrics": metrics,
        "yield_curve": results["yield_curve"],
        "spread_history": results["spread_history"],
        "quality_checks": quality,
        "summary": build_summary(metrics, labels, kinds),
    }


def main():
    as_of = datetime.now(ZoneInfo("America/Toronto")).date()
    payload = fetch_observations(SERIES_IDS, start_date=as_of - timedelta(days=HISTORY_DAYS))
    rows = parse_observations(payload, SERIES_IDS)
    print(f"Fetched {len(rows)} observations for {len(SERIES_IDS)} series (one request).")

    data = build_payload(rows, as_of)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=1, default=to_json) + "\n")

    for check in data["quality_checks"]:
        print(f"  [{check['status'].upper():4}] {check['check_name']}: {check['message']}")
    print(f"Summary ({data['summary']['source']}): {data['summary']['text']}")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
