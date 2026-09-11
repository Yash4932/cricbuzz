"""
config.py
---------
Centralized configuration for Cricbuzz LiveStats.
Reads secrets from environment variables (via a local .env file, never committed).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
def _get_secret(key: str, default: str = "") -> str:
    """Env var first, then Streamlit Cloud's st.secrets, then default."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default

BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Cricbuzz API (RapidAPI) configuration
# ---------------------------------------------------------------------------
CRICBUZZ_API_KEY = _get_secret("CRICBUZZ_API_KEY", "")
CRICBUZZ_API_HOST = _get_secret("CRICBUZZ_API_HOST", "cricbuzz-cricket.p.rapidapi.com")
CRICBUZZ_BASE_URL = f"https://{CRICBUZZ_API_HOST}"

CRICBUZZ_HEADERS = {
    "x-rapidapi-key": CRICBUZZ_API_KEY,
    "x-rapidapi-host": CRICBUZZ_API_HOST,
}

API_CONFIGURED = bool(CRICBUZZ_API_KEY)

# ---------------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------------
# The app is written to be database-agnostic. Out of the box it runs on
# SQLite (zero setup, ships with seeded demo data). Set DB_ENGINE=postgres
# or DB_ENGINE=mysql and fill in the matching env vars to point it at a
# real server instead -- utils/db_connection.py handles the branching.
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()

SQLITE_PATH = os.getenv("SQLITE_PATH", str(BASE_DIR / "data" / "cricbuzz_livestats.db"))

POSTGRES_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "dbname": os.getenv("PG_DB", "cricbuzz_livestats"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", ""),
}

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": os.getenv("MYSQL_PORT", "3306"),
    "database": os.getenv("MYSQL_DB", "cricbuzz_livestats"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
}

# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------
APP_TITLE = "Cricbuzz LiveStats"
APP_ICON = "🏏"
APP_TAGLINE = "Real-Time Cricket Insights & SQL-Based Analytics"
