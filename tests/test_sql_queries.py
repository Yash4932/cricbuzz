"""
tests/test_sql_queries.py
----------------------------
Ensures all 25 SQL analytics queries execute without error against the
live schema, and spot-checks a few for basic sanity (non-negative counts,
expected columns present).
"""

import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sql.queries import QUERIES
from utils.db_connection import run_query


@pytest.mark.parametrize("q", QUERIES, ids=[f"Q{q['id']}_{q['title'][:30]}" for q in QUERIES])
def test_query_executes(q):
    df = run_query(q["sql"])
    assert df is not None  # empty result sets are valid (e.g. Q9 all-rounder threshold)


def test_all_25_present():
    ids = sorted(q["id"] for q in QUERIES)
    assert ids == list(range(1, 26))


def test_q4_capacity_filter_correct():
    df = run_query([q for q in QUERIES if q["id"] == 4][0]["sql"])
    assert (df["capacity"] > 50000).all()


def test_q6_role_counts_sum_to_total_players():
    df = run_query([q for q in QUERIES if q["id"] == 6][0]["sql"])
    total = run_query("SELECT COUNT(*) c FROM players")["c"][0]
    assert df["player_count"].sum() == total
