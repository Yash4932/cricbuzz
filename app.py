"""
app.py
-------
Router / entry point. Uses Streamlit's st.navigation + st.Page API so that
every page's sidebar label, icon, and URL slug is set explicitly in code
(never inferred from a filename) -- filenames containing emoji are a known
source of mojibake on Windows when Streamlit auto-derives nav labels from
them, so view files use plain ASCII names and all display text lives here.
"""

import streamlit as st

import config
from utils.theme import apply_theme

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

try:
    st.logo("assets/logo.svg", icon_image="assets/icon.svg")
except Exception:
    pass  # older Streamlit versions without st.logo -- fail silently, app still works

home_page = st.Page("views/home.py", title="Home", icon="🏠", default=True, url_path="home")
live_page = st.Page("views/live_matches.py", title="Live Matches", icon="🔴", url_path="live-matches")
stats_page = st.Page("views/top_player_stats.py", title="Top Player Stats", icon="📊", url_path="top-player-stats")
sql_page = st.Page("views/sql_analytics.py", title="SQL Analytics", icon="🧮", url_path="sql-analytics")
crud_page = st.Page("views/crud_operations.py", title="CRUD Operations", icon="✏️", url_path="crud-operations")

pg = st.navigation(
    {
        "Overview": [home_page],
        "Modules": [live_page, stats_page, sql_page, crud_page],
    }
)
pg.run()
