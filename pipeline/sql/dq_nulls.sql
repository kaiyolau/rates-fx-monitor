-- Null values: dates where the API returned an empty value.
-- warn: any null (rows are skipped by the transforms, so results stay usable).
WITH per_series AS (
    SELECT series, COUNT(*) FILTER (WHERE value IS NULL) AS nulls
    FROM observations
    GROUP BY series
)
SELECT
    'Null values' AS check_name,
    CASE WHEN COALESCE(SUM(nulls), 0) = 0 THEN 'pass' ELSE 'warn' END AS status,
    CASE
        WHEN COALESCE(SUM(nulls), 0) = 0 THEN 'No empty values across ' || COUNT(*) || ' series.'
        ELSE SUM(nulls) || ' empty value(s): '
             || string_agg(series || ' (' || nulls || ')', ', ' ORDER BY series) FILTER (WHERE nulls > 0) || '.'
    END AS message
FROM per_series;
