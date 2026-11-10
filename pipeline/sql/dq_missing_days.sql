-- Missing business days in the last 90 calendar days, up to the latest observation.
-- A weekday counts as an "open day" if at least two series reported on it.
-- A weekday with at most one series is treated as a holiday, not a gap: the policy
-- rate (V39079) is published even on statutory holidays when markets are closed.
-- A series is missing a day when it did not report on an open day.
-- Days after a series' last observation are left to the stale-data check.
-- pass: no gaps; warn: worst series has 1-3 gaps; fail: worst series has more.
WITH window_days AS (
    SELECT CAST(d AS DATE) AS day
    FROM generate_series(CAST($as_of AS DATE) - INTERVAL 89 DAY, CAST($as_of AS DATE), INTERVAL 1 DAY) AS g(d)
    WHERE isodow(d) <= 5
      AND d <= (SELECT MAX(date) FROM observations)
),
open_days AS (
    SELECT w.day
    FROM window_days AS w
    JOIN observations AS o ON o.date = w.day
    GROUP BY w.day
    HAVING COUNT(DISTINCT o.series) >= 2
),
holidays AS (
    SELECT day FROM window_days
    EXCEPT
    SELECT day FROM open_days
),
spans AS (
    SELECT series, MIN(date) AS first_date, MAX(date) AS last_date
    FROM observations
    GROUP BY series
),
gaps AS (
    SELECT s.series, COUNT(*) AS missing
    FROM spans AS s
    JOIN open_days AS d
      ON d.day BETWEEN s.first_date AND s.last_date
    LEFT JOIN observations AS o
      ON o.series = s.series AND o.date = d.day
    WHERE o.series IS NULL
    GROUP BY s.series
)
SELECT
    'Missing business days' AS check_name,
    CASE
        WHEN COALESCE(MAX(missing), 0) = 0 THEN 'pass'
        WHEN MAX(missing) <= 3 THEN 'warn'
        ELSE 'fail'
    END AS status,
    CASE
        WHEN COALESCE(MAX(missing), 0) = 0 THEN 'No gaps in the last 90 days'
        ELSE 'Gaps in the last 90 days: '
             || string_agg(series || ' (' || missing || ')', ', ' ORDER BY series)
    END
    || ' (' || (SELECT COUNT(*) FROM holidays) || ' weekday(s) treated as holidays).'
    AS message
FROM gaps;
