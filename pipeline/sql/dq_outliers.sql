-- Outliers: unusually large day-over-day moves in the last 90 calendar days.
-- Compares each observation with the previous non-null observation.
-- Rates: absolute move above 0.50 percentage points (a 50 bp policy move is not flagged).
-- FX: move above 3 percent. NULLIF guards against division by zero.
-- warn only: a big move can be real news, so a human should look at it.
WITH changes AS (
    SELECT
        o.series,
        s.kind,
        o.date,
        o.value - LAG(o.value) OVER w                                  AS diff,
        100 * (o.value - LAG(o.value) OVER w) / NULLIF(LAG(o.value) OVER w, 0) AS pct
    FROM observations AS o
    JOIN series AS s ON s.series = o.series
    WHERE o.value IS NOT NULL
    WINDOW w AS (PARTITION BY o.series ORDER BY o.date)
),
jumps AS (
    SELECT *
    FROM changes
    WHERE date > CAST($as_of AS DATE) - INTERVAL 90 DAY
      AND ((kind = 'rate' AND ABS(diff) > 0.5)
        OR (kind = 'fx'   AND ABS(pct)  > 3))
)
SELECT
    'Outliers (large daily jumps)' AS check_name,
    CASE WHEN COUNT(*) = 0 THEN 'pass' ELSE 'warn' END AS status,
    CASE
        WHEN COUNT(*) = 0 THEN 'No daily move above 0.50 pp (rates) or 3% (FX) in the last 90 days.'
        ELSE COUNT(*) || ' large move(s) to review: '
             || string_agg(series || ' on ' || strftime(date, '%Y-%m-%d'), ', ' ORDER BY date) || '.'
    END AS message
FROM jumps;
