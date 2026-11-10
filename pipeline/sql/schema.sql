-- Raw data: one row per (series, date). No primary key on purpose,
-- so the duplicate-date check can detect bad loads.
CREATE TABLE series (
    series      VARCHAR,
    label       VARCHAR,
    kind        VARCHAR,   -- 'rate' (percent) or 'fx' (CAD per unit of foreign currency)
    tenor_years INTEGER    -- set for benchmark bond yields only
);

CREATE TABLE observations (
    series VARCHAR,
    date   DATE,
    value  DOUBLE          -- NULL when the API returned an empty value
);

-- 10Y minus 2Y spread, in percentage points, on dates where both yields exist.
CREATE VIEW spread_10y_2y AS
SELECT
    'SPREAD_10Y_2Y'        AS series,
    y10.date               AS date,
    y10.value - y2.value   AS value
FROM observations AS y10
JOIN observations AS y2
  ON y2.date = y10.date
 AND y2.series = 'BD.CDN.2YR.DQ.YLD'
WHERE y10.series = 'BD.CDN.10YR.DQ.YLD';

-- Raw series plus the derived spread, used by the transforms.
CREATE VIEW metric_values AS
SELECT series, date, value FROM observations
UNION ALL
SELECT series, date, value FROM spread_10y_2y;
