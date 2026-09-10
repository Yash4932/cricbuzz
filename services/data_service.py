"""
services/data_service.py
--------------------------
CRUD operations for the Player Analytics module, plus read helpers for
Match records used across the dashboard. Every write is validated before
it touches the database and wrapped so a bad request never leaves the
table in a half-written state.
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from utils.db_connection import get_connection, run_query


VALID_ROLES = {"Batsman", "Bowler", "All-rounder", "Wicket-keeper"}


class ValidationError(Exception):
    """Raised when incoming CRUD data fails a business rule check."""


@dataclass
class PlayerInput:
    full_name: str
    country: str
    playing_role: str
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO 'YYYY-MM-DD'

    def validate(self):
        if not self.full_name or not self.full_name.strip():
            raise ValidationError("Full name is required.")
        if not self.country or not self.country.strip():
            raise ValidationError("Country is required.")
        if self.playing_role not in VALID_ROLES:
            raise ValidationError(f"Playing role must be one of {sorted(VALID_ROLES)}.")
        if self.date_of_birth:
            try:
                pd.to_datetime(self.date_of_birth)
            except Exception:
                raise ValidationError("Date of birth must be a valid date.")


# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------
def list_players(search: str = "", role: str = "All", country: str = "All",
                  limit: int = 200, offset: int = 0) -> pd.DataFrame:
    clauses = []
    params: list = []

    if search:
        clauses.append("full_name LIKE ?")
        params.append(f"%{search}%")
    if role != "All":
        clauses.append("playing_role = ?")
        params.append(role)
    if country != "All":
        clauses.append("country = ?")
        params.append(country)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT player_id, full_name, country, playing_role,
               batting_style, bowling_style, date_of_birth
        FROM players
        {where_sql}
        ORDER BY full_name
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    return run_query(sql, tuple(params))


def get_player(player_id: int) -> Optional[dict]:
    df = run_query("SELECT * FROM players WHERE player_id = ?", (player_id,))
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def distinct_countries() -> list:
    df = run_query("SELECT DISTINCT country FROM players ORDER BY country")
    return df["country"].tolist()


def player_count() -> int:
    df = run_query("SELECT COUNT(*) AS c FROM players")
    return int(df["c"][0])


# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
def create_player(data: PlayerInput) -> int:
    data.validate()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO players
               (full_name, country, playing_role, batting_style, bowling_style, date_of_birth)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data.full_name.strip(), data.country.strip(), data.playing_role,
             data.batting_style, data.bowling_style, data.date_of_birth or None),
        )
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
def update_player(player_id: int, data: PlayerInput) -> bool:
    data.validate()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE players SET
               full_name = ?, country = ?, playing_role = ?,
               batting_style = ?, bowling_style = ?, date_of_birth = ?
               WHERE player_id = ?""",
            (data.full_name.strip(), data.country.strip(), data.playing_role,
             data.batting_style, data.bowling_style, data.date_of_birth or None, player_id),
        )
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def delete_player(player_id: int) -> bool:
    """
    Deletes a player. Career scorecards referencing this player are left
    untouched by design (no ON DELETE CASCADE on players) -- a player's
    historical stats shouldn't vanish just because their master record is
    removed. If you need hard-delete-everything semantics, delete the
    scorecard rows explicitly first.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        # Check for dependent scorecards and warn via return value rather
        # than silently orphaning foreign keys.
        cur.execute("SELECT COUNT(*) FROM batting_scorecards WHERE player_id = ?", (player_id,))
        has_history = cur.fetchone()[0] > 0
        if has_history:
            raise ValidationError(
                "This player has historical match records and cannot be deleted. "
                "Remove their scorecards first, or archive instead of deleting."
            )
        cur.execute("DELETE FROM players WHERE player_id = ?", (player_id,))
        conn.commit()
        return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
