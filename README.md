# Rates & FX Monitor

A one-page dashboard of Canadian interest rates and exchange rates, built from the Bank of
Canada's public [Valet API](https://www.bankofcanada.ca/valet/docs). It shows the policy rate,
2Y and 10Y Government of Canada yields, USD/CAD, a yield curve, the 10Y minus 2Y spread, a
plain-language summary and the results of data-quality checks.

**Live demo:** LIVE_URL_PLACEHOLDER

Unofficial demo using Bank of Canada public data. Not a Bank of Canada product.

## Architecture

```
GitHub Actions (weekdays 23:00 UTC)
        |
        v
pipeline/run.py ── 1 HTTP request ──> Bank of Canada Valet API
        |
        |  rows (series, date, value)
        v
DuckDB (in memory) ── pipeline/sql/*.sql
        |   transforms: latest values, 1D/1M/1Y changes, 10Y-2Y spread, yield curve
        |   data quality: stale, missing days, outliers, nulls, duplicates
        v
summary: Claude (optional) ── grounding check ──> pass? else rule-based template
        |
        v
web/public/data.json ── git commit ──> Vercel build ──> static React page
                                                       (reads data.json only)
```

## Run locally

```bash
pip install -r requirements.txt
python -m pipeline.run
cd web && npm install && npm run dev
```

Tests: `python -m pytest` and `cd web && npm test`. Set `ANTHROPIC_API_KEY` to try the
AI-written summary; without it the rule-based summary is used.

## Series

| Series | Valet name |
|---|---|
| Policy interest rate | `V39079` |
| CORRA | `AVG.INTWO` |
| GoC benchmark yields 2Y / 5Y / 10Y | `BD.CDN.2YR.DQ.YLD`, `BD.CDN.5YR.DQ.YLD`, `BD.CDN.10YR.DQ.YLD` |
| USD/CAD, EUR/CAD, GBP/CAD | `FXUSDCAD`, `FXEURCAD`, `FXGBPCAD` |

Names were confirmed against the live `lists/series` endpoint.

## Design decisions

- **Why static JSON.** The data changes once a day, so there is nothing to compute per visit.
  A pre-built `data.json` means no server, no database, no secrets in the browser, nothing to
  keep running, and the page loads instantly for anyone with the link.
- **Why DuckDB.** Real SQL (window functions, ASOF joins for "value on or before a date") in a
  single pip package with no server. The transforms and data-quality rules are plain `.sql`
  files that can be read and reviewed on their own.
- **Why a rule-based fallback for the AI text.** The demo must work without an API key, and
  a dashboard must never show a wrong number. Claude's text is used only if every number in
  it matches the source data; otherwise, or with no key, a template built directly from the
  data is shown. The badge next to the summary says which one you are reading.

## Data-quality checks

Each check is one SQL file in `pipeline/sql/` and returns pass / warn / fail with a message.

| Check | Rule |
|---|---|
| Stale data | Business days since each series' last value: pass ≤ 2, warn ≤ 5, fail otherwise |
| Missing business days | Last 90 days. A weekday with at most one series reporting is a holiday (the policy rate is published on holidays); otherwise a series without a value has a gap. warn 1–3 gaps, fail more |
| Outliers | Daily move above 0.50 pp (rates) or 3% (FX) in the last 90 days: warn |
| Null values | Empty values returned by the API: warn |
| Duplicate dates | Same series and date twice: fail |

## AI workflow

Built with Claude Code using a plan, implement, review, test loop. Project rules for the AI
are in [CLAUDE.md](CLAUDE.md), the reusable data-quality review is in
[.claude/commands/review.md](.claude/commands/review.md), and
[AI_WORKFLOW.md](AI_WORKFLOW.md) logs the mistakes the AI made and how each was caught.
`tests/test_grounding.py` is a small evaluation of the AI-summary grounding check
(made-up number, correct summary, rounding).

## Deployment

- **Data:** `.github/workflows/update-data.yml` runs the tests and the pipeline every weekday
  and commits `web/public/data.json`. Add an `ANTHROPIC_API_KEY` repository secret to enable
  the AI summary (optional).
- **Site:** Vercel, connected to this repo. `vercel.json` builds `web/` and serves `web/dist`.
  Every push, including the daily data commit, redeploys. No environment variables needed.
- **CI:** `.github/workflows/ci.yml` runs pytest, Vitest and the production build on every push.

Data: [Bank of Canada](https://www.bankofcanada.ca/), used under the
[terms of use](https://www.bankofcanada.ca/terms/).
