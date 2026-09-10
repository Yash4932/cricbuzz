"""
tests/test_crud.py
--------------------
Tests for the CRUD service layer (Create/Read/Update/Delete on players),
including validation rules and delete-protection for players with history.
"""

import sys
from pathlib import Path
import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.data_service import (
    create_player, update_player, delete_player, get_player, list_players,
    PlayerInput, ValidationError,
)


@pytest.fixture
def temp_player():
    pid = create_player(PlayerInput(
        full_name="Pytest Temp Player", country="Testland", playing_role="Batsman",
    ))
    yield pid
    # cleanup if the test didn't already delete it
    try:
        delete_player(pid)
    except Exception:
        pass


def test_create_and_read(temp_player):
    rec = get_player(temp_player)
    assert rec is not None
    assert rec["full_name"] == "Pytest Temp Player"
    assert rec["playing_role"] == "Batsman"


def test_update(temp_player):
    ok = update_player(temp_player, PlayerInput(
        full_name="Pytest Temp Player Updated", country="Testland", playing_role="Bowler",
    ))
    assert ok
    rec = get_player(temp_player)
    assert rec["full_name"] == "Pytest Temp Player Updated"
    assert rec["playing_role"] == "Bowler"


def test_delete(temp_player):
    ok = delete_player(temp_player)
    assert ok
    assert get_player(temp_player) is None


def test_empty_name_rejected():
    with pytest.raises(ValidationError):
        create_player(PlayerInput(full_name="  ", country="India", playing_role="Batsman"))


def test_invalid_role_rejected():
    with pytest.raises(ValidationError):
        create_player(PlayerInput(full_name="Someone", country="India", playing_role="Wizard"))


def test_invalid_dob_rejected():
    with pytest.raises(ValidationError):
        create_player(PlayerInput(
            full_name="Someone", country="India", playing_role="Batsman",
            date_of_birth="not-a-date",
        ))


def test_delete_protected_for_players_with_history():
    df = list_players(limit=1)
    real_id = int(df.iloc[0]["player_id"])
    with pytest.raises(ValidationError):
        delete_player(real_id)


def test_update_nonexistent_player_returns_false():
    ok = update_player(999999999, PlayerInput(
        full_name="Ghost", country="Nowhere", playing_role="Batsman",
    ))
    assert ok is False
