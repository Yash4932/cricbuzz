"""
pages/1_Live_Matches.py
-------------------------
Pulls live / recent / upcoming matches from the Cricbuzz API. If no API
key is configured, shows clear setup instructions instead of an error
screen, plus a preview of what the seeded historical data looks like so
the page still demonstrates something meaningful.
"""

import streamlit as st

import config
from utils.theme import hero_banner, live_badge, thin_divider
from utils.db_connection import run_query
from services.api_service import get_live_matches, get_recent_matches, get_upcoming_matches, ApiError

hero_banner("Live Matches", "Real-time scores, straight from the Cricbuzz API", "🔴")

if not config.API_CONFIGURED:
    st.warning(
        "**Cricbuzz API key not configured.** This page needs live data from RapidAPI to show "
        "real matches. Here's how to enable it:"
    )
    st.markdown(
        """
        1. Create a free account at [RapidAPI's Cricbuzz Cricket API](https://rapidapi.com/cricbuzz-cricbuzz-default/api/cricbuzz-cricket)
        2. Subscribe to the free tier and copy your `X-RapidAPI-Key`
        3. Copy `.env.example` to `.env` in the project root
        4. Set `CRICBUZZ_API_KEY=your_key_here`
        5. Restart the app
        """
    )
    thin_divider()
    st.markdown("### In the meantime — here's what's live in the seeded warehouse")
    demo = run_query(
        """
        SELECT m.match_description, t1.team_name AS team1, t2.team_name AS team2,
               v.venue_name, m.match_status, m.match_date
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        JOIN venues v ON m.venue_id = v.venue_id
        WHERE m.match_status IN ('live', 'upcoming')
        ORDER BY m.match_date DESC
        LIMIT 10
        """
    )
    if demo.empty:
        st.info("No live/upcoming rows in the seeded data right now — try re-running the seed script.")
    else:
        for _, row in demo.iterrows():
            with st.container():
                cols = st.columns([3, 2, 2])
                with cols[0]:
                    if row["match_status"] == "live":
                        live_badge()
                    st.markdown(f"**{row['match_description']}**")
                    st.caption(row["venue_name"])
                with cols[1]:
                    st.markdown(f"{row['team1']} vs {row['team2']}")
                with cols[2]:
                    st.caption(str(row["match_date"]))
        st.caption(
            "Note: this demo table is synthetic seeded data (for the SQL analytics module), "
            "not a live feed — real live scores appear here once an API key is set."
        )
    st.stop()

# ---------------------------------------------------------------------------
# Live API mode
# ---------------------------------------------------------------------------
tab_live, tab_recent, tab_upcoming = st.tabs(["🔴 Live", "✅ Recent", "🗓️ Upcoming"])

with tab_live:
    try:
        data = get_live_matches()
        type_matches = data.get("typeMatches", [])
        if not type_matches:
            st.info("No live matches right now. Check back during an active series.")
        for tm in type_matches:
            st.markdown(f"#### {tm.get('matchType', '')}")
            for series_block in tm.get("seriesMatches", []):
                series_data = series_block.get("seriesAdWrapper", {})
                for match in series_data.get("matches", []):
                    info = match.get("matchInfo", {})
                    live_badge()
                    st.markdown(f"**{info.get('matchDesc', '')} — {info.get('team1', {}).get('teamName','')} vs "
                                f"{info.get('team2', {}).get('teamName','')}**")
                    st.caption(f"{info.get('venueInfo', {}).get('ground','')}, "
                               f"{info.get('venueInfo', {}).get('city','')}")
                    thin_divider()
    except ApiError as e:
        st.error(str(e))

with tab_recent:
    try:
        data = get_recent_matches()
        type_matches = data.get("typeMatches", [])
        if not type_matches:
            st.info("No recent matches found.")
        for tm in type_matches:
            for series_block in tm.get("seriesMatches", []):
                series_data = series_block.get("seriesAdWrapper", {})
                for match in series_data.get("matches", []):
                    info = match.get("matchInfo", {})
                    st.markdown(f"**{info.get('matchDesc','')}** — "
                                f"{info.get('team1', {}).get('teamName','')} vs "
                                f"{info.get('team2', {}).get('teamName','')}")
                    st.caption(info.get("status", ""))
                    thin_divider()
    except ApiError as e:
        st.error(str(e))

with tab_upcoming:
    try:
        data = get_upcoming_matches()
        type_matches = data.get("typeMatches", [])
        if not type_matches:
            st.info("No upcoming matches found.")
        for tm in type_matches:
            for series_block in tm.get("seriesMatches", []):
                series_data = series_block.get("seriesAdWrapper", {})
                for match in series_data.get("matches", []):
                    info = match.get("matchInfo", {})
                    st.markdown(f"**{info.get('matchDesc','')}** — "
                                f"{info.get('team1', {}).get('teamName','')} vs "
                                f"{info.get('team2', {}).get('teamName','')}")
                    st.caption(f"Starts: {info.get('startDate','TBD')}")
                    thin_divider()
    except ApiError as e:
        st.error(str(e))
