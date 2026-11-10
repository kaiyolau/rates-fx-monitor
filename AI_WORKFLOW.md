# AI workflow

This repo was built with Claude Code (an AI coding assistant). This file records how the
work was done and every real mistake the AI made that was caught along the way.

## The loop

1. **Plan.** Write a short plan and confirm facts first. Example: before writing any
   pipeline code, the Valet `lists/series` endpoint and each `series/<name>` endpoint were
   called to confirm the real series names.
2. **Implement** one step at a time, in order: pipeline, tests, front end, CI, docs.
3. **Review.** Run the step against real data and read the output; look at the page in a
   browser at desktop and mobile widths; run the `/review` checklist
   (`.claude/commands/review.md`) on the data-quality SQL.
4. **Test.** `python -m pytest` and `npm test` / `npm run build` before calling a step done.
   Both run in CI on every push.

Rules the AI follows are in [CLAUDE.md](CLAUDE.md).

## What was not delegated

- Metrics and data-quality rules are plain SQL in `pipeline/sql/` with thresholds written in
  comments, so each rule can be explained without trusting the AI.
- The AI summary is optional. Every number in it must match the source data
  (`pipeline/summary.py`, tested in `tests/test_grounding.py`); otherwise a rule-based
  template is shown.

## Mistakes the AI made and how they were caught

Only real incidents from building this repo are listed.

| # | Mistake | How it was caught | Fix |
|---|---------|-------------------|-----|
| 1 | The missing-business-day check treated a weekday as "open" if *any* series reported. The policy rate (V39079) is published on statutory holidays, so Labour Day, the National Day for Truth and Reconciliation and Thanksgiving 2026 showed up as gaps in 7 series. | First run against the live API returned WARN. Listing the affected dates showed they were all holidays. | Changed the open-day rule; added `test_holiday_reported_only_by_policy_rate_is_not_a_gap`. Confirmed the test fails on the old rule. |
| 2 | The same check counted the run date itself as a holiday, because today's data is not published yet. | Same investigation: the message said "1 weekday with no data" and that day was today. | The check window now ends at the latest observation. |
| 3 | The fix for #1 over-corrected: a "majority of series" rule meant a partial outage (5 of 8 series missing a day) was silently treated as a holiday. | Running the `/review` checklist edge case "partial outage" on a small fixture: the check said pass. | A holiday is now a weekday where at most one series reported; added `test_partial_outage_is_a_gap_not_a_holiday`. |
| 4 | The rule-based summary said "rose 1 bps". | Reading the pipeline output. | Singular "bp" for 1. |
| 5 | The "Last updated" formatter combined `dateStyle`/`timeStyle` with `timeZoneName`, which `Intl` rejects, so the page crashed on render. | The Vitest render test failed with `TypeError: Invalid option`. | Listed the date and time fields explicitly. |
| 6 | Yield-curve chart: uneven y-axis ticks (4.1%, 3.7%, 3.2%), legend sorted alphabetically instead of Today / 1 month / 1 year, and dashed lines drawing dashed outlines on the dots. | Screenshot review in a browser. | Rounded axis domain, explicit legend order, solid dots. |

## Known limits

- The Claude path was built against the SDK's documented parameters and exercised with an
  invalid key (it fell back to the template as designed), but no real Claude summary had been
  generated when this was written, because no API key was configured.
- The grounding check verifies numbers, not wording: a summary that says "rose" for a fall
  with the right number would pass. The template computes direction from the data.
