"""
pages/2_Top_Player_Stats.py
------------------------------
Leaderboards and visual stats: top run scorers, top wicket takers, role
distribution, format comparison. Uses the seeded historical warehouse
(deep multi-year stats aren't something a live API can provide), plus a
live ICC-rankings pull if an API key is configured.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from utils.theme import hero_banner, thin_divider
from utils.db_connection import run_query
from services.api_service import get_icc_rankings, ApiError


def _normalize_rankings(payload: dict) -> pd.DataFrame | None:
    """
    The Cricbuzz rankings endpoint nests the actual list of players under
    varying keys depending on rankingType ('rank', 'rankings', etc.) and
    field names vary slightly by endpoint version. This pulls out whatever
    list-of-dicts it can find and normalizes it into a clean table instead
    of dumping raw JSON at the user.
    """
    candidates = []
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        for key in ("rank", "rankings", "player", "players", "data"):
            val = payload.get(key)
            if isinstance(val, list) and val:
                candidates = val
                break

    if not candidates:
        return None

    df = pd.json_normalize(candidates)

    # Best-effort column renaming for common Cricbuzz field variants. More than
    # one source key can map to the same target (e.g. both "name" and
    # "fullName" present in the same response) which would otherwise leave
    # duplicate column names and crash Streamlit's arrow serialization -- so
    # after renaming, any duplicates get coalesced into a single column
    # (first non-null value wins) instead of just blindly renaming.
    rename_map = {
        "rank": "Rank", "ranking": "Rank",
        "name": "Player", "playerName": "Player", "fullName": "Player",
        "rating": "Rating", "points": "Rating",
        "country": "Team", "team": "Team", "teamName": "Team",
        "trend": "Trend", "difference": "Change", "rankingChange": "Change",
        "lastUpdatedOn": "Updated",
    }
    # Internal API bookkeeping fields -- not meaningful to someone reading a
    # leaderboard, so drop them outright rather than showing raw ids.
    drop_cols = {"id", "faceImageId", "countryId"}
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if df.columns.duplicated().any():
        coalesced = {}
        for col_name in pd.unique(df.columns):
            subset = df.loc[:, df.columns == col_name]
            coalesced[col_name] = subset.bfill(axis=1).iloc[:, 0] if subset.shape[1] > 1 else subset.iloc[:, 0]
        df = pd.DataFrame(coalesced)

    preferred_order = [c for c in ["Rank", "Player", "Team", "Rating", "Trend", "Change", "Updated"] if c in df.columns]
    other_cols = [c for c in df.columns if c not in preferred_order]
    df = df[preferred_order + other_cols]
    return df

hero_banner("Top Player Stats", "Leaderboards across runs, wickets, and formats", "📊")

format_choice = st.selectbox("Format", ["ODI", "Test", "T20I"], index=0)

# ---------------------------------------------------------------------------
# Top run scorers
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 🏏 Top 10 Run Scorers")
    runs_df = run_query(
        """
        SELECT p.full_name,
               SUM(b.runs_scored) AS total_runs,
               ROUND2(SUM(b.runs_scored)*1.0 /
                   NULLIF(SUM(CASE WHEN b.dismissal_type <> 'not out' THEN 1 ELSE 0 END),0), 2) AS batting_average
        FROM batting_scorecards b
        JOIN players p ON b.player_id = p.player_id
        JOIN matches m ON b.match_id = m.match_id
        WHERE m.match_type = ?
        GROUP BY p.player_id
        ORDER BY total_runs DESC
        LIMIT 10
        """,
        (format_choice,),
    )
    if not runs_df.empty:
        fig = px.bar(
            runs_df.sort_values("total_runs"), x="total_runs", y="full_name",
            orientation="h", text="total_runs",
            color="total_runs", color_continuous_scale=["#081310", "#12734A", "#E8C468"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="white", showlegend=False, coloraxis_showscale=False,
            xaxis_title="Total Runs", yaxis_title="", height=420,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data for this format yet.")

with col2:
    st.markdown("#### 🎯 Top 10 Wicket Takers")
    wickets_df = run_query(
        """
        SELECT p.full_name,
               SUM(bo.wickets_taken) AS total_wickets,
               ROUND2(SUM(bo.runs_conceded)*1.0/NULLIF(SUM(bo.overs_bowled),0), 2) AS economy_rate
        FROM bowling_scorecards bo
        JOIN players p ON bo.player_id = p.player_id
        JOIN matches m ON bo.match_id = m.match_id
        WHERE m.match_type = ?
        GROUP BY p.player_id
        ORDER BY total_wickets DESC
        LIMIT 10
        """,
        (format_choice,),
    )
    if not wickets_df.empty:
        fig = px.bar(
            wickets_df.sort_values("total_wickets"), x="total_wickets", y="full_name",
            orientation="h", text="total_wickets",
            color="total_wickets", color_continuous_scale=["#081310", "#0F5132", "#D4AF37"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font_color="white", showlegend=False, coloraxis_showscale=False,
            xaxis_title="Total Wickets", yaxis_title="", height=420,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No data for this format yet.")

thin_divider()

# ---------------------------------------------------------------------------
# Role distribution + highest scores per format
# ---------------------------------------------------------------------------
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### 🧩 Player Role Distribution")
    role_df = run_query("SELECT playing_role, COUNT(*) AS cnt FROM players GROUP BY playing_role")
    fig = px.pie(
        role_df, names="playing_role", values="cnt", hole=0.55,
        color_discrete_sequence=["#D4AF37", "#12734A", "#E8C468", "#2FBF71"],
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="white", height=380, margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=-0.1),
    )
    st.plotly_chart(fig, width='stretch')

with col4:
    st.markdown("#### 🏆 Highest Individual Score by Format")
    hs_df = run_query(
        """
        SELECT m.match_type AS format, MAX(b.runs_scored) AS highest_score
        FROM batting_scorecards b JOIN matches m ON b.match_id = m.match_id
        GROUP BY m.match_type
        """
    )
    fig = go.Figure(go.Bar(
        x=hs_df["format"], y=hs_df["highest_score"],
        marker_color=["#D4AF37", "#12734A", "#E8C468"], text=hs_df["highest_score"],
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font_color="white", height=380, margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="Runs",
    )
    st.plotly_chart(fig, width='stretch')

thin_divider()

# ---------------------------------------------------------------------------
# Live ICC rankings (API-backed)
# ---------------------------------------------------------------------------
st.markdown("#### 🌐 Live ICC Rankings")
if not config.API_CONFIGURED:
    st.info(
        "Live ICC rankings need a Cricbuzz API key — add `CRICBUZZ_API_KEY` to your `.env` "
        "file to pull these directly from Cricbuzz. (See the Live Matches page for setup steps.)"
    )
else:
    rc1, rc2 = st.columns(2)
    with rc1:
        rank_type = st.selectbox("Ranking type", ["batsmen", "bowlers", "allrounders"], key="rank_type")
    with rc2:
        rank_category = st.selectbox("Category", ["men", "women"], key="rank_category")

    try:
        rankings = get_icc_rankings(format_type=rank_type, category=rank_category)
        table = _normalize_rankings(rankings)
        if table is not None and not table.empty:
            st.dataframe(table.head(25), width="stretch", hide_index=True)
            if "Updated" in table.columns and not table["Updated"].isna().all():
                st.caption(
                    f"📡 Live from Cricbuzz — last updated **{table['Updated'].iloc[0]}**. "
                    "This pulls fresh from the API on every page load, so it reflects "
                    "whatever ICC's current rankings are whenever you check back."
                )
            else:
                st.caption("📡 Live from Cricbuzz — refreshed on every page load.")
        else:
            st.warning("Couldn't find a recognizable ranking list in the API response.")
            with st.expander("Show raw response"):
                st.json(rankings, expanded=False)
    except ApiError as e:
        st.error(str(e))
