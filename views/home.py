"""
views/home.py
--------------
Home / overview page content. Rendered by app.py via st.navigation.
"""

import streamlit as st

import config
from utils.theme import hero_banner, stat_chip, thin_divider, seam_divider
from utils.db_connection import run_query

hero_banner(config.APP_TITLE, config.APP_TAGLINE)

try:
    counts = {}
    for label, table in [
        ("Players", "players"), ("Teams", "teams"), ("Venues", "venues"),
        ("Series", "series"), ("Matches", "matches"),
    ]:
        counts[label] = int(run_query(f"SELECT COUNT(*) c FROM {table}")["c"][0])

    cols = st.columns(5)
    for col, (label, val) in zip(cols, counts.items()):
        with col:
            stat_chip(label, f"{val:,}")
except Exception as e:
    st.warning(f"Database not seeded yet. Run `python data/seed_data.py` first. ({e})")

seam_divider()

st.markdown("### Explore the app")

c1, c2 = st.columns(2)
with c1:
    st.markdown(
        """
        <div class="glass-card">
        <h4>🔴 Live Matches</h4>
        <p>Pull live scores, in-progress scorecards, and recently completed
        matches straight from the Cricbuzz API (requires an API key).</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        """
        <div class="glass-card">
        <h4>🧮 SQL Analytics</h4>
        <p>All 25 practice questions from beginner to advanced &mdash; each with
        the business framing, the query, and a line-by-line explanation,
        run live against the seeded database.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        """
        <div class="glass-card">
        <h4>📊 Top Player Stats</h4>
        <p>Leaderboards for runs, wickets, and batting/bowling records,
        blending live API data with the historical warehouse.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        """
        <div class="glass-card">
        <h4>✏️ CRUD Operations</h4>
        <p>Full create / read / update / delete on the player roster through
        a validated, form-based UI &mdash; the database management module.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

thin_divider()

left, right = st.columns([1.3, 1])

with left:
    st.markdown("### Tech stack")
    st.markdown(
        "`Python` &nbsp; `Streamlit` &nbsp; `SQL (SQLite / PostgreSQL / MySQL)` "
        "&nbsp; `REST API` &nbsp; `pandas` &nbsp; `requests` &nbsp; `Plotly`"
    )
    st.markdown("### Project structure")
    st.code(
        """cricbuzz_livestats/
├── app.py                  # Router (st.navigation)
├── config.py                # Env-driven configuration
├── views/                   # Page content
│   ├── home.py
│   ├── live_matches.py
│   ├── top_player_stats.py
│   ├── sql_analytics.py
│   └── crud_operations.py
├── services/
│   ├── api_service.py        # Cricbuzz API wrapper
│   └── data_service.py       # CRUD + validation
├── utils/
│   ├── db_connection.py      # Engine-agnostic DB layer
│   └── theme.py               # Custom CSS / UI helpers
├── database/schema.sql       # Normalized schema
├── sql/queries.py             # The 25 analytics queries
└── data/seed_data.py          # Synthetic data generator""",
        language="text",
    )

with right:
    st.markdown("### API status")
    if config.API_CONFIGURED:
        st.success("Cricbuzz API key detected — Live Matches and Top Stats will use live data.")
    else:
        st.info(
            "No Cricbuzz API key found yet. Live Matches / Top Stats pages will show "
            "setup instructions instead of erroring out.\n\n"
            "Add `CRICBUZZ_API_KEY` to a `.env` file (see `.env.example`) to enable them."
        )
    st.markdown("### Database engine")
    st.markdown(f"Currently running on: **`{config.DB_ENGINE}`**")
    st.caption(
        "Switch engines by setting `DB_ENGINE=postgres` or `DB_ENGINE=mysql` in `.env` "
        "— every query in this app goes through utils/db_connection.py, so nothing "
        "else needs to change."
    )

st.caption("Built as a learning project · Sports Analytics domain · Cricbuzz LiveStats")
