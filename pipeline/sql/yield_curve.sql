-- Yield-curve snapshot: each benchmark yield today, 1 month ago and 1 year ago.
-- "Today" is the latest date with any bond yield; each point uses the most
-- recent observation on or before the reference date (ASOF join).
WITH yields AS (
    SELECT o.series, o.date, o.value
    FROM observations AS o
    JOIN series AS s ON s.series = o.series
    WHERE s.tenor_years IS NOT NULL
      AND o.value IS NOT NULL
),
ref AS (
    SELECT MAX(date) AS today FROM yields
),
targets AS (
    SELECT
        s.series,
        s.tenor_years,
        r.today,
        CAST(r.today - INTERVAL 1 MONTH AS DATE) AS month_ago,
        CAST(r.today - INTERVAL 1 YEAR  AS DATE) AS year_ago
    FROM series AS s
    CROSS JOIN ref AS r
    WHERE s.tenor_years IS NOT NULL
)
SELECT
    t.tenor_years || 'Y' AS tenor,
    t.tenor_years,
    a.date  AS today_date,
    a.value AS today,
    m.date  AS month_ago_date,
    m.value AS month_ago,
    y.date  AS year_ago_date,
    y.value AS year_ago
FROM targets AS t
ASOF LEFT JOIN yields AS a ON a.series = t.series AND t.today     >= a.date
ASOF LEFT JOIN yields AS m ON m.series = t.series AND t.month_ago >= m.date
ASOF LEFT JOIN yields AS y ON y.series = t.series AND t.year_ago  >= y.date
ORDER BY t.tenor_years;
