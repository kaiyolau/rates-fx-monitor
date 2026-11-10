-- Stale data: business days between each series' last non-null observation
-- and the run date ($as_of). Weekends are not counted. Holidays are counted,
-- so a holiday can add one day of lag; the thresholds leave room for that.
-- pass: every series <= 2 business days behind
-- warn: worst series 3-5 business days behind
-- fail: worst series > 5 business days behind, or a series has no data at all
WITH last_obs AS (
    SELECT s.series, MAX(o.date) AS last_date
    FROM series AS s
    LEFT JOIN observations AS o
      ON o.series = s.series AND o.value IS NOT NULL
    GROUP BY s.series
),
weekdays AS (
    SELECT CAST(d AS DATE) AS day
    FROM generate_series(CAST($as_of AS DATE) - INTERVAL 60 DAY, CAST($as_of AS DATE), INTERVAL 1 DAY) AS g(d)
    WHERE isodow(d) <= 5          -- Monday..Friday
),
lag AS (
    SELECT l.series, l.last_date, COUNT(w.day) AS lag_days
    FROM last_obs AS l
    LEFT JOIN weekdays AS w ON w.day > l.last_date
    GROUP BY l.series, l.last_date
),
flagged AS (
    SELECT
        series,
        last_date,
        lag_days,
        CASE
            WHEN last_date IS NULL THEN 'fail'
            WHEN lag_days > 5 THEN 'fail'
            WHEN lag_days > 2 THEN 'warn'
            ELSE 'pass'
        END AS status
    FROM lag
)
SELECT
    'Stale data' AS check_name,
    CASE
        WHEN COUNT(*) FILTER (WHERE status = 'fail') > 0 THEN 'fail'
        WHEN COUNT(*) FILTER (WHERE status = 'warn') > 0 THEN 'warn'
        ELSE 'pass'
    END AS status,
    CASE
        WHEN COUNT(*) FILTER (WHERE status <> 'pass') = 0
            THEN 'All ' || COUNT(*) || ' series updated within 2 business days (latest: '
                 || strftime(MAX(last_date), '%Y-%m-%d') || ').'
        ELSE 'Behind schedule: ' || string_agg(
                 series || CASE WHEN last_date IS NULL THEN ' (no data)'
                                ELSE ' (' || lag_days || ' business days)' END,
                 ', ' ORDER BY series) FILTER (WHERE status <> 'pass') || '.'
    END AS message
FROM flagged;
