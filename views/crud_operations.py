"""
pages/4_CRUD_Operations.py
-----------------------------
Full Create / Read / Update / Delete on the player roster, through a
validated, form-based UI. This is the database-management module of the
project.
"""

import streamlit as st

from utils.theme import hero_banner, thin_divider
from services.data_service import (
    list_players, get_player, distinct_countries, player_count,
    create_player, update_player, delete_player,
    PlayerInput, ValidationError, VALID_ROLES,
)

hero_banner("Player Analytics — CRUD", "Create, read, update, and delete player records", "✏️")

tab_read, tab_create, tab_update, tab_delete = st.tabs(
    ["📋 Browse", "➕ Add Player", "✏️ Update", "🗑️ Delete"]
)

# ---------------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------------
with tab_read:
    st.markdown(f"**{player_count():,} players** in the database.")
    c1, c2, c3 = st.columns(3)
    with c1:
        search = st.text_input("Search by name", "")
    with c2:
        role_filter = st.selectbox("Filter by role", ["All"] + sorted(VALID_ROLES))
    with c3:
        country_filter = st.selectbox("Filter by country", ["All"] + distinct_countries())

    df = list_players(search=search, role=role_filter, country=country_filter, limit=300)
    st.dataframe(df, width='stretch', height=460)
    st.caption(f"Showing {len(df):,} matching player(s).")

thin_divider()

# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
with tab_create:
    st.markdown("#### Add a new player")
    with st.form("create_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            full_name = st.text_input("Full name *")
            country = st.text_input("Country *")
            role = st.selectbox("Playing role *", sorted(VALID_ROLES))
        with c2:
            batting_style = st.selectbox("Batting style", ["Right-hand bat", "Left-hand bat", ""])
            bowling_style = st.selectbox(
                "Bowling style",
                ["", "Right-arm fast", "Right-arm fast-medium", "Left-arm fast",
                 "Right-arm off break", "Left-arm orthodox", "Legbreak googly"],
            )
            dob = st.date_input("Date of birth", value=None)

        submitted = st.form_submit_button("Create player")
        if submitted:
            try:
                data = PlayerInput(
                    full_name=full_name, country=country, playing_role=role,
                    batting_style=batting_style or None, bowling_style=bowling_style or None,
                    date_of_birth=dob.isoformat() if dob else None,
                )
                new_id = create_player(data)
                st.success(f"Created player #{new_id}: {full_name}")
            except ValidationError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Unexpected error: {e}")

thin_divider()

# ---------------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------------
with tab_update:
    st.markdown("#### Update an existing player")
    player_id = st.number_input("Player ID to update", min_value=1, step=1, key="update_id")
    if st.button("Load player"):
        record = get_player(int(player_id))
        if record is None:
            st.error(f"No player found with ID {player_id}.")
            st.session_state.pop("loaded_player", None)
        else:
            st.session_state["loaded_player"] = record

    if "loaded_player" in st.session_state:
        record = st.session_state["loaded_player"]
        with st.form("update_form"):
            c1, c2 = st.columns(2)
            with c1:
                full_name = st.text_input("Full name *", value=record["full_name"])
                country = st.text_input("Country *", value=record["country"])
                role_options = sorted(VALID_ROLES)
                role = st.selectbox(
                    "Playing role *", role_options,
                    index=role_options.index(record["playing_role"]) if record["playing_role"] in role_options else 0,
                )
            with c2:
                batting_style = st.text_input("Batting style", value=record.get("batting_style") or "")
                bowling_style = st.text_input("Bowling style", value=record.get("bowling_style") or "")
                dob_val = record.get("date_of_birth")
                dob = st.text_input("Date of birth (YYYY-MM-DD)", value=dob_val or "")

            submitted = st.form_submit_button("Save changes")
            if submitted:
                try:
                    data = PlayerInput(
                        full_name=full_name, country=country, playing_role=role,
                        batting_style=batting_style or None, bowling_style=bowling_style or None,
                        date_of_birth=dob or None,
                    )
                    ok = update_player(int(record["player_id"]), data)
                    if ok:
                        st.success(f"Updated player #{record['player_id']}.")
                        st.session_state.pop("loaded_player", None)
                    else:
                        st.warning("No rows were updated — the player may have been deleted.")
                except ValidationError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

thin_divider()

# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
with tab_delete:
    st.markdown("#### Delete a player")
    st.caption(
        "Players with existing batting scorecards (historical match data) are protected "
        "from deletion to preserve data integrity — remove their scorecards first if you "
        "really need to delete them."
    )
    del_id = st.number_input("Player ID to delete", min_value=1, step=1, key="delete_id")
    confirm = st.checkbox("I understand this action cannot be undone.")
    if st.button("🗑️ Delete player", disabled=not confirm):
        try:
            ok = delete_player(int(del_id))
            if ok:
                st.success(f"Deleted player #{del_id}.")
            else:
                st.warning(f"No player found with ID {del_id}.")
        except ValidationError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Unexpected error: {e}")
