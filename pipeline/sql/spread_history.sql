-- Daily 10Y minus 2Y spread (percentage points) for the last year of data.
SELECT
    date,
    ROUND(value, 4) AS spread
FROM spread_10y_2y
WHERE value IS NOT NULL
  AND date > (
      SELECT CAST(MAX(date) - INTERVAL 1 YEAR AS DATE)
      FROM spread_10y_2y
      WHERE value IS NOT NULL
  )
ORDER BY date;
