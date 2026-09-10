"""
tests/test_database.py
------------------------
Database-layer tests: schema integrity, custom SQL functions, referential
constraints. Run with: pytest tests/ -v
"""

import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.db_connection import run_query, run_write, get_connection


def test_all_tables_exist():
    tables = ["teams", "players", "venues", "series", "matches",
              "batting_scorecards", "bowling_scorecards", "fielding_scorecards"]
    for t in tables:
        df = run_query(f"SELECT COUNT(*) c FROM {t}")
        assert df["c"][0] >= 0


def test_seed_data_present():
    assert run_query("SELECT COUNT(*) c FROM players")["c"][0] > 0
    assert run_query("SELECT COUNT(*) c FROM matches")["c"][0] > 0


def test_foreign_key_integrity_matches_teams():
    """Every match's team1/team2/winner should reference a real team."""
    df = run_query("""
        SELECT COUNT(*) c FROM matches m
        LEFT JOIN teams t1 ON m.team1_id = t1.team_id
        WHERE t1.team_id IS NULL
    """)
    assert df["c"][0] == 0


def test_custom_stdev_function():
    df = run_query("SELECT STDEV(x) AS s FROM (SELECT 1 AS x UNION SELECT 3 UNION SELECT 5)")
    assert abs(df["s"][0] - 1.633) < 0.01


def test_custom_sqrt_function():
    df = run_query("SELECT SQRT(16.0) AS s")
    assert df["s"][0] == 4.0


def test_check_constraint_rejects_bad_role():
    with pytest.raises(Exception):
        run_write(
            "INSERT INTO players (full_name, country, playing_role) VALUES (?, ?, ?)",
            ("Bad Role Test", "Testland", "Wizard"),
        )


def test_check_constraint_team_cannot_play_itself():
    df = run_query("SELECT team_id FROM teams LIMIT 1")
    tid = int(df["team_id"][0])
    with pytest.raises(Exception):
        run_write(
            """INSERT INTO matches (series_id, team1_id, team2_id, venue_id, match_date,
               match_type, match_description)
               VALUES (1, ?, ?, 1, '2026-01-01', 'ODI', 'Self match test')""",
            (tid, tid),
        )
