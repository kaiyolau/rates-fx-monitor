-- Duplicate dates: the same (series, date) loaded more than once.
-- fail: any duplicate (the transforms would double count).
WITH dupes AS (
    SELECT series, date, COUNT(*) AS n
    FROM observations
    GROUP BY series, date
    HAVING COUNT(*) > 1
)
SELECT
    'Duplicate dates' AS check_name,
    CASE WHEN COUNT(*) = 0 THEN 'pass' ELSE 'fail' END AS status,
    CASE
        WHEN COUNT(*) = 0 THEN 'No series has the same date twice.'
        ELSE COUNT(*) || ' duplicated series/date pair(s), e.g. '
             || MIN(series || ' on ' || strftime(date, '%Y-%m-%d')) || '.'
    END AS message
FROM dupes;
