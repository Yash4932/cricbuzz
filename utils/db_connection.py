"""
utils/db_connection.py
-----------------------
Centralized, engine-agnostic database connection handling.

Design goal (per project spec): keep every other module ignorant of which
SQL engine is actually running underneath. Everything talks to
`get_connection()` / `run_query()` / `run_write()` and doesn't care whether
the backend is SQLite, PostgreSQL, or MySQL.

SQLite is the default because it needs zero external setup -- perfect for a
learning project and for grading/demo purposes. Because SQLite has no
built-in STDEV()/VARIANCE() (needed by the advanced SQL questions), we
register small custom SQL functions on every SQLite connection so the
analytics queries can use standard-looking SQL.
"""

import math
import sqlite3
import contextlib
import pandas as pd

import config


# ---------------------------------------------------------------------------
# Custom aggregate: population standard deviation, usable as STDEV(col) in SQL
# ---------------------------------------------------------------------------
class _StdevAggregate:
    def __init__(self):
        self.values = []

    def step(self, value):
        if value is not None:
            self.values.append(value)

    def finalize(self):
        n = len(self.values)
        if n < 2:
            return 0.0
        mean = sum(self.values) / n
        variance = sum((v - mean) ** 2 for v in self.values) / n
        return math.sqrt(variance)


def _register_sqlite_functions(conn: sqlite3.Connection) -> None:
    conn.create_function("SQRT", 1, lambda x: math.sqrt(x) if x is not None and x >= 0 else None)
    conn.create_function("POWER", 2, lambda x, y: (x ** y) if x is not None else None)
    conn.create_aggregate("STDEV", 1, _StdevAggregate)
    conn.create_function(
        "ROUND2",
        2,
        lambda x, n: round(x, n) if x is not None else None,
    )


def get_connection():
    """Return a live connection for the configured engine."""
    engine = config.DB_ENGINE

    if engine == "sqlite":
        conn = sqlite3.connect(config.SQLITE_PATH, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        _register_sqlite_functions(conn)
        return conn

    if engine == "postgres":
        import psycopg2
        cfg = config.POSTGRES_CONFIG
        return psycopg2.connect(
            host=cfg["host"], port=cfg["port"], dbname=cfg["dbname"],
            user=cfg["user"], password=cfg["password"],
        )

    if engine == "mysql":
        import mysql.connector
        cfg = config.MYSQL_CONFIG
        return mysql.connector.connect(
            host=cfg["host"], port=cfg["port"], database=cfg["database"],
            user=cfg["user"], password=cfg["password"],
        )

    raise ValueError(f"Unsupported DB_ENGINE: {engine}")


@contextlib.contextmanager
def get_cursor(commit: bool = False):
    """Context manager yielding a cursor; commits and closes automatically."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


def run_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a SELECT and return the results as a DataFrame."""
    conn = get_connection()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()


def run_write(sql: str, params: tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE. Returns rows affected."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def run_script(sql_script: str) -> None:
    """Execute a multi-statement SQL script (schema creation, etc.)."""
    conn = get_connection()
    try:
        if config.DB_ENGINE == "sqlite":
            conn.executescript(sql_script)
            conn.commit()
        else:
            cur = conn.cursor()
            for statement in filter(None, (s.strip() for s in sql_script.split(";"))):
                cur.execute(statement)
            conn.commit()
    finally:
        conn.close()
