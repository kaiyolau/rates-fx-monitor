"""Load observations into an in-memory DuckDB and run the SQL files in pipeline/sql."""

from datetime import date
from pathlib import Path

import duckdb

from pipeline.series import SERIES

SQL_DIR = Path(__file__).parent / "sql"

QUALITY_CHECKS = [
    ("dq_stale.sql", True),          # (file, needs $as_of)
    ("dq_missing_days.sql", True),
    ("dq_outliers.sql", True),
    ("dq_nulls.sql", False),
    ("dq_duplicates.sql", False),
]


def read_sql(name: str) -> str:
    return (SQL_DIR / name).read_text()


def load_db(rows, series=SERIES) -> duckdb.DuckDBPyConnection:
    """Create the schema and insert (series, date, value) rows."""
    con = duckdb.connect()
    con.execute(read_sql("schema.sql"))
    con.executemany("INSERT INTO series VALUES (?, ?, ?, ?)", list(series))
    if rows:
        con.executemany("INSERT INTO observations VALUES (?, ?, ?)", list(rows))
    return con


def query(con, name: str, params: dict | None = None) -> list[dict]:
    """Run one SQL file and return its rows as dicts."""
    cursor = con.execute(read_sql(name), params) if params else con.execute(read_sql(name))
    columns = [c[0] for c in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def compute_metrics(con) -> dict:
    return {
        "metrics": query(con, "latest_metrics.sql"),
        "yield_curve": query(con, "yield_curve.sql"),
        "spread_history": query(con, "spread_history.sql"),
    }


def run_quality_checks(con, as_of: date) -> list[dict]:
    results = []
    for name, needs_as_of in QUALITY_CHECKS:
        params = {"as_of": as_of} if needs_as_of else None
        results.extend(query(con, name, params))
    return results
