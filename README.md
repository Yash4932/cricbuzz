# 🏏 Cricbuzz LiveStats: Real-Time Cricket Insights & SQL-Based Analytics

Live app: https://yscricbuzz.streamlit.app/

A comprehensive cricket analytics dashboard built with **Python, Streamlit, SQL, and the Cricbuzz REST API**. Combines live match data, a normalized relational database, 25 progressively advanced SQL analytics queries, and full CRUD operations into one premium-styled web app.

**Domain:** Sports Analytics
**Skills demonstrated:** Python · SQL · Streamlit · JSON · REST API integration · Database design

---

## ✨ Features

| Module | What it does |
|---|---|
| 🔴 **Live Matches** | Real-time scores, scorecards, and match status via the Cricbuzz API |
| 📊 **Top Player Stats** | Interactive leaderboards for runs, wickets, and format records with Plotly charts, plus live ICC rankings |
| 🧮 **SQL Analytics** | All 25 practice questions (Beginner → Advanced), each runnable live with business context and explanations |
| ✏️ **CRUD Operations** | Full Create/Read/Update/Delete on the player roster with validation and delete-protection |

The UI uses a custom dark, gradient-driven "sports broadcast" theme: animated drifting glow orbs in the background, a shimmering gradient hero banner, glassmorphic cards with hover-lift, a pulsing LIVE indicator, a branded logo, and a signature stitched-seam (cricket ball) divider motif — see `utils/theme.py`.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# (optional) edit .env and add your Cricbuzz API key — see "Live API setup" below

# 3. Generate the database (SQLite by default, zero setup required)
python data/seed_data.py

# 4. Run the app
streamlit run app.py
```

The app works fully **without** an API key — the SQL Analytics, Top Player Stats (historical), and CRUD modules all run against the seeded local database. Only the Live Matches page (and live ICC rankings) need a Cricbuzz API key.

### Live API setup (optional)
1. Create a free account at [RapidAPI's Cricbuzz Cricket API](https://rapidapi.com/cricbuzz-cricbuzz-default/api/cricbuzz-cricket)
2. Subscribe to the free tier and copy your `X-RapidAPI-Key`
3. In `.env`, set `CRICBUZZ_API_KEY=your_key_here`
4. Restart the app

---

## 🗂️ Project Structure

```
cricbuzz_livestats/
├── app.py                        # Router (st.navigation / st.Page) + theme init
├── config.py                     # Env-driven configuration (API keys, DB engine)
├── requirements.txt
├── .env.example                  # Copy to .env and fill in secrets
├── .streamlit/config.toml        # Theme + server config
│
├── assets/
│   ├── logo.svg                   # Sidebar wordmark
│   └── icon.svg                   # Collapsed-sidebar icon
│
├── views/                        # Page content (plain filenames -- see note below)
│   ├── home.py
│   ├── live_matches.py
│   ├── top_player_stats.py
│   ├── sql_analytics.py
│   └── crud_operations.py
│
├── services/
│   ├── api_service.py             # Cricbuzz API wrapper (retries, error handling)
│   └── data_service.py            # CRUD logic + validation for players
│
├── utils/
│   ├── db_connection.py           # Engine-agnostic DB layer (SQLite/Postgres/MySQL)
│   └── theme.py                    # Custom CSS + reusable UI components
│
├── database/
│   └── schema.sql                 # Normalized relational schema (3NF)
│
├── sql/
│   └── queries.py                 # All 25 SQL practice questions + metadata
│
├── data/
│   ├── seed_data.py               # Synthetic multi-season data generator
│   └── cricbuzz_livestats.db      # Generated SQLite database (after running seed script)
│
└── tests/
    ├── test_database.py
    ├── test_crud.py
    └── test_sql_queries.py
```

> **Why `views/` instead of Streamlit's usual `pages/` folder?** Streamlit's legacy convention auto-derives each page's sidebar label and URL slug from its filename. Emoji in filenames (e.g. `1_🔴_Live_Matches.py`) can get mis-decoded on Windows, producing garbled sidebar text and broken URLs. This app instead uses the modern `st.Page` / `st.navigation` API in `app.py`, where every title, icon, and URL slug is set explicitly in code — plain ASCII filenames throughout, zero encoding surface.

---

## 🗄️ Database Design

Normalized to **3NF** — no repeating groups, no partial/transitive dependencies. Eight tables:

- **teams** — international teams
- **players** — roster with role, batting/bowling style
- **venues** — grounds with city/country/capacity
- **series** — tours/series with format and date range
- **matches** — one row per match, references teams (×3 roles: team1, team2, winner), venue, series
- **batting_scorecards** — one row per player per innings per match (runs, balls, position, dismissal)
- **bowling_scorecards** — one row per player per innings per match (overs, runs conceded, wickets)
- **fielding_scorecards** — catches/stumpings per player per match

Deliberately **no precomputed career-totals table** — every aggregate (career runs, batting average, economy rate, etc.) is derived at query time from the raw scorecards. This keeps the schema fully normalized and is exactly what the 25 SQL questions are designed to exercise.

Indexes are placed on every foreign key and on frequently filtered columns (`match_date`, `match_type`, `country`, `playing_role`). CHECK constraints enforce valid enums (`playing_role`, `match_type`, `victory_type`) and business rules (a team can't play itself).

### Why synthetic seed data?
The Cricbuzz API only exposes *current* data — it has no endpoint for "give me 6 years of ball-by-ball history for 200 players," which several of the 25 SQL questions require (year-over-year trends, quarterly form, 3-year head-to-head). `data/seed_data.py` generates a realistic, internally consistent multi-season dataset (2019–2026, 12 teams, ~217 players, 260 matches, ~6,700 batting innings) so every query — including the advanced ones — returns meaningful results out of the box. The Live Matches page still uses the real API when a key is configured.

### Switching database engines
Everything goes through `utils/db_connection.py`. To point the app at Postgres or MySQL instead of SQLite:
```
# .env
DB_ENGINE=postgres   # or mysql
PG_HOST=...
PG_DB=...
PG_USER=...
PG_PASSWORD=...
```
Then run the schema against that server (`psql -f database/schema.sql`, adjusting `AUTOINCREMENT`→`SERIAL`/`AUTO_INCREMENT` for the target dialect) and re-run `seed_data.py`.

---

## 🧮 The 25 SQL Questions

All stored in `sql/queries.py` with business framing + explanation, organized by difficulty:

- **Beginner (1–8):** SELECT, WHERE, GROUP BY, ORDER BY
- **Intermediate (9–16):** JOINs, CTEs, subqueries, aggregate functions
- **Advanced (17–25):** window functions (`RANK`, `ROW_NUMBER`, `COUNT() OVER`), CTEs, a custom `STDEV()` aggregate (SQLite has no built-in standard deviation — registered in `utils/db_connection.py`), weighted scoring formulas, and time-series analysis

Every query has been executed against the live seeded database and verified to run without error (see `tests/test_sql_queries.py`).

---

## ✅ Testing

```bash
pip install pytest
pytest tests/ -v
```

43 tests covering:
- Schema integrity, foreign keys, CHECK constraints, custom SQL functions
- CRUD create/read/update/delete + validation rules + delete-protection
- All 25 analytics queries execute successfully + spot-check assertions

---

## 🌐 Deployment

**Streamlit Community Cloud** (simplest):
1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo, set main file to `app.py`
3. Add `CRICBUZZ_API_KEY` etc. under Settings → Secrets (as `secrets.toml` format)
4. Note: SQLite on Streamlit Cloud is ephemeral — run `seed_data.py` as a one-off startup step, or switch to a managed Postgres (e.g. via Supabase/Neon) for persistence.

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN python data/seed_data.py
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

**Render / Railway:** connect the GitHub repo, set the start command to
`python data/seed_data.py && streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`, and add environment variables from `.env.example`.

---

## 📋 Deliverables Checklist

- [x] Source code — complete modular Python application
- [x] Database schema — normalized SQL tables (`database/schema.sql`)
- [x] Sample/seed data — realistic multi-season synthetic dataset
- [x] Documentation — this README + inline docstrings throughout
- [x] Requirements — `requirements.txt`
- [x] Working demo — all 4 modules functional (Live Matches, Top Stats, SQL Analytics, CRUD)
- [x] SQL Practice — all 25 questions (8 beginner / 8 intermediate / 9 advanced), implemented and explained
- [ ] Recording video — record a walkthrough of the running app for submission

---

## 🛠️ Coding standards followed
PEP 8 formatting · docstrings on every module/function · modular separation (services / utils / pages / sql) · parameterized queries everywhere (no SQL injection surface) · try/except with rollback on every write · `.env`-based secrets (never hardcoded, `.env` itself is gitignored).
