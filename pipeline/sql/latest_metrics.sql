-- Latest value per series and its change vs. 1 day, 1 month and 1 year earlier.
-- Each comparison uses the most recent observation ON OR BEFORE the target date
-- (ASOF join), so weekends and holidays are skipped automatically.
-- Changes are in the series' own unit: percentage points for rates, CAD for FX.
WITH clean AS (
    SELECT series, date, value
    FROM metric_values
    WHERE value IS NOT NULL
),
latest AS (
    SELECT series, MAX(date) AS latest_date
    FROM clean
    GROUP BY series
),
targets AS (
    SELECT
        series,
        latest_date,
        CAST(latest_date - INTERVAL 1 DAY   AS DATE) AS day_ago,
        CAST(latest_date - INTERVAL 1 MONTH AS DATE) AS month_ago,
        CAST(latest_date - INTERVAL 1 YEAR  AS DATE) AS year_ago
    FROM latest
)
SELECT
    t.series,
    t.latest_date,
    cur.value                                              AS latest_value,
    d.date                                                 AS prev_date,
    ROUND(cur.value - d.value, 6)                          AS change_1d,
    ROUND(cur.value - m.value, 6)                          AS change_1m,
    ROUND(cur.value - y.value, 6)                          AS change_1y,
    -- NULLIF avoids division by zero when the earlier value is 0.
    ROUND(100 * (cur.value - d.value) / NULLIF(d.value, 0), 4) AS pct_change_1d,
    ROUND(100 * (cur.value - m.value) / NULLIF(m.value, 0), 4) AS pct_change_1m,
    ROUND(100 * (cur.value - y.value) / NULLIF(y.value, 0), 4) AS pct_change_1y
FROM targets AS t
JOIN clean AS cur
  ON cur.series = t.series AND cur.date = t.latest_date
ASOF LEFT JOIN clean AS d
  ON d.series = t.series AND t.day_ago >= d.date
ASOF LEFT JOIN clean AS m
  ON m.series = t.series AND t.month_ago >= m.date
ASOF LEFT JOIN clean AS y
  ON y.series = t.series AND t.year_ago >= y.date
ORDER BY t.series;
