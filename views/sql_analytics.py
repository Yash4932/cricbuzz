"""
pages/3_SQL_Analytics.py
---------------------------
The analytics heart of the project: all 25 SQL practice questions,
grouped by difficulty, each showing the business framing, the query
itself, a plain-English explanation, and live results run against the
seeded database. A free-form custom SQL box at the bottom lets you run
your own SELECT statements against the same schema.
"""

import streamlit as st
import pandas as pd

from utils.theme import hero_banner, level_pill, thin_divider
from utils.db_connection import run_query
from sql.queries import QUERIES, LEVELS

hero_banner("SQL Queries & Analytics", "25 practice questions, from basic filters to window functions", "🧮")

tabs = st.tabs([f"🟢 {LEVELS[0]}", f"🟡 {LEVELS[1]}", f"🔴 {LEVELS[2]}", "✍️ Custom Query"])

for tab, level in zip(tabs[:3], LEVELS):
    with tab:
        level_queries = [q for q in QUERIES if q["level"] == level]
        for q in level_queries:
            with st.expander(f"**Q{q['id']}. {q['title']}**"):
                level_pill(q["level"])
                st.markdown(f"**Business problem:** {q['business_problem']}")
                st.markdown(f"**SQL concepts used:** {q['concepts']}")

                st.markdown("**Query:**")
                st.code(q["sql"], language="sql")

                st.markdown("**How it works:**")
                st.markdown(q["explanation"])

                run_key = f"run_{q['id']}"
                if st.button("▶ Run this query", key=run_key):
                    try:
                        df = run_query(q["sql"])
                        st.session_state[f"result_{q['id']}"] = df
                    except Exception as e:
                        st.error(f"Query failed: {e}")

                if f"result_{q['id']}" in st.session_state:
                    df = st.session_state[f"result_{q['id']}"]
                    st.dataframe(df, width='stretch', height=min(400, 45 + 35 * len(df)))
                    st.caption(f"{len(df):,} row(s) returned.")
                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "⬇ Download CSV", csv, file_name=f"query_{q['id']}_results.csv",
                        mime="text/csv", key=f"dl_{q['id']}",
                    )

thin_divider()

with tabs[3]:
    st.markdown("#### Run your own query")
    st.caption(
        "Read-only sandbox against the live schema (teams, players, venues, series, "
        "matches, batting_scorecards, bowling_scorecards, fielding_scorecards). "
        "Only SELECT / WITH statements are allowed here."
    )
    default_sql = "SELECT * FROM players LIMIT 10;"
    user_sql = st.text_area("SQL", value=default_sql, height=160)

    if st.button("▶ Run", key="run_custom"):
        stripped = user_sql.strip().lower()
        if not (stripped.startswith("select") or stripped.startswith("with")):
            st.error("Only SELECT / WITH (read-only) statements are allowed in this sandbox.")
        else:
            try:
                df = run_query(user_sql)
                st.dataframe(df, width='stretch')
                st.caption(f"{len(df):,} row(s) returned.")
            except Exception as e:
                st.error(f"Query failed: {e}")

    with st.expander("📋 Schema reference"):
        st.code(
            """teams(team_id, team_name, country)
players(player_id, full_name, country, playing_role, batting_style, bowling_style, date_of_birth)
venues(venue_id, venue_name, city, country, capacity)
series(series_id, series_name, host_country, match_type, start_date, total_matches)
matches(match_id, series_id, team1_id, team2_id, venue_id, match_date, match_type,
        match_description, winner_team_id, victory_margin, victory_type,
        toss_winner_id, toss_decision, match_status)
batting_scorecards(scorecard_id, match_id, innings_number, player_id, team_id,
                    batting_position, runs_scored, balls_faced, fours, sixes, dismissal_type)
bowling_scorecards(scorecard_id, match_id, innings_number, player_id, team_id,
                    overs_bowled, runs_conceded, wickets_taken)
fielding_scorecards(scorecard_id, match_id, player_id, team_id, catches, stumpings)

-- Custom functions available: STDEV(x), SQRT(x), POWER(x,y), ROUND2(x,n)""",
            language="sql",
        )
