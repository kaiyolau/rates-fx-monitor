---
description: Review the data-quality SQL for edge cases
---

Review the data-quality checks in `pipeline/sql/dq_*.sql` (and the transforms they rely on in
`pipeline/sql/latest_metrics.sql`). For each file, read the SQL and answer the questions below.
Where an answer is unclear, prove it: build a tiny fixture with `pipeline.analytics.load_db`
and run `run_quality_checks` on it. Do not change tests to make a check pass.

## Checklist

1. **Weekends and holidays**
   - Are weekends excluded everywhere business days are counted (`isodow(d) <= 5`)?
   - What happens on a statutory holiday? Remember the policy rate (V39079) is published on
     holidays when markets are closed. Is a holiday ever reported as a gap?
   - What happens when the run date (`$as_of`) is a Saturday or Sunday?

2. **Missing days**
   - Is a partial outage (several series missing the same day) reported, or does it look like a holiday?
   - Is a series with no rows at all caught by some check?
   - Are days after a series' last observation double counted (missing *and* stale)?

3. **Stale data**
   - Is lag measured from the last *non-null* value?
   - Does today's not-yet-published data cause a false warning?
   - Are the pass / warn / fail thresholds stated in a comment and in the message?

4. **Divisions by zero and nulls**
   - Is every division guarded with `NULLIF(x, 0)`?
   - Do `LAG` / ASOF lookups skip NULL values, or can a NULL leak into a change?
   - Do aggregates behave on an empty table (`COUNT`, `MAX`, `string_agg` return NULL)?

5. **Readability**
   - Can a non-engineer follow each check from its header comment alone?

## Output

A short list: file, the edge case, what happens today (with the fixture you ran), and a
suggested fix. Then run `python -m pytest -q` and report the result.
