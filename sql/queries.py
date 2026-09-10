"""
sql/queries.py
---------------
The 25 SQL practice questions from the project spec, each stored as a
structured record: level, business framing, the SQL itself, and a plain
English explanation of the logic. Consumed by pages/4_SQL_Analytics.py.

Levels: Beginner (1-8) -> basic SELECT/WHERE/GROUP BY/ORDER BY
        Intermediate (9-16) -> JOINs, subqueries, aggregates
        Advanced (17-25) -> window functions, CTEs, analytical calculations
"""

QUERIES = [
    # ------------------------------------------------------------------ #
    # BEGINNER
    # ------------------------------------------------------------------ #
    {
        "id": 1, "level": "Beginner",
        "title": "Indian players and their playing profile",
        "business_problem": "A broadcaster wants a quick roster of every Indian "
            "player with their role and batting/bowling style for commentary notes.",
        "concepts": "Simple SELECT + WHERE filter",
        "sql": """
SELECT full_name, playing_role, batting_style, bowling_style
FROM players
WHERE country = 'India'
ORDER BY full_name;
""".strip(),
        "explanation": "Filters the players table down to one country using a plain "
            "WHERE clause -- no joins needed since everything asked for lives in one table.",
    },
    {
        "id": 2, "level": "Beginner",
        "title": "Matches played in the last 30 days",
        "business_problem": "Fans and commentators want a quick recap of recent fixtures.",
        "concepts": "JOINs across matches/teams/venues, date filtering, ORDER BY",
        "sql": """
SELECT
    m.match_description,
    t1.team_name AS team1,
    t2.team_name AS team2,
    v.venue_name || ', ' || v.city AS venue,
    m.match_date
FROM matches m
JOIN teams t1  ON m.team1_id = t1.team_id
JOIN teams t2  ON m.team2_id = t2.team_id
JOIN venues v  ON m.venue_id = v.venue_id
WHERE m.match_date >= date('now', '-30 days')
ORDER BY m.match_date DESC;
""".strip(),
        "explanation": "Three joins bring in human-readable team and venue names; "
            "SQLite's date('now','-30 days') computes the rolling cutoff at query time.",
    },
    {
        "id": 3, "level": "Beginner",
        "title": "Top 10 ODI run scorers",
        "business_problem": "Pre-match graphics need a 'most runs in ODIs' leaderboard.",
        "concepts": "Aggregate functions (SUM), derived batting average, GROUP BY, LIMIT",
        "sql": """
SELECT
    p.full_name,
    SUM(b.runs_scored) AS total_runs,
    ROUND2(SUM(b.runs_scored) * 1.0 /
        NULLIF(SUM(CASE WHEN b.dismissal_type <> 'not out' THEN 1 ELSE 0 END), 0), 2) AS batting_average,
    SUM(CASE WHEN b.runs_scored >= 100 THEN 1 ELSE 0 END) AS centuries
FROM batting_scorecards b
JOIN players p ON b.player_id = p.player_id
JOIN matches m ON b.match_id = m.match_id
WHERE m.match_type = 'ODI'
GROUP BY p.player_id
ORDER BY total_runs DESC
LIMIT 10;
""".strip(),
        "explanation": "Batting average = runs / times dismissed (NULLIF guards a "
            "divide-by-zero for players who were never out). Centuries counted via a "
            "conditional SUM (a 0/1 indicator summed per player).",
    },
    {
        "id": 4, "level": "Beginner",
        "title": "Venues with capacity over 50,000",
        "business_problem": "Event planners want the shortlist of 'big stadium' venues.",
        "concepts": "WHERE + ORDER BY on a single table",
        "sql": """
SELECT venue_name, city, country, capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC;
""".strip(),
        "explanation": "Straightforward filter and sort -- no joins required.",
    },
    {
        "id": 5, "level": "Beginner",
        "title": "Total wins per team",
        "business_problem": "A quick team-strength leaderboard for the home page.",
        "concepts": "JOIN + GROUP BY + COUNT",
        "sql": """
SELECT t.team_name, COUNT(*) AS total_wins
FROM matches m
JOIN teams t ON m.winner_team_id = t.team_id
GROUP BY t.team_id
ORDER BY total_wins DESC;
""".strip(),
        "explanation": "Joining matches to teams on winner_team_id and counting rows "
            "per team gives total wins directly.",
    },
    {
        "id": 6, "level": "Beginner",
        "title": "Player count by playing role",
        "business_problem": "Squad-balance check: how many bowlers vs batsmen exist in the pool.",
        "concepts": "GROUP BY + COUNT",
        "sql": """
SELECT playing_role, COUNT(*) AS player_count
FROM players
GROUP BY playing_role
ORDER BY player_count DESC;
""".strip(),
        "explanation": "One aggregate, one group-by column -- the simplest possible "
            "GROUP BY pattern.",
    },
    {
        "id": 7, "level": "Beginner",
        "title": "Highest individual score per format",
        "business_problem": "Trivia / record-book style stat for the Top Stats page.",
        "concepts": "GROUP BY + MAX",
        "sql": """
SELECT m.match_type AS format, MAX(b.runs_scored) AS highest_score
FROM batting_scorecards b
JOIN matches m ON b.match_id = m.match_id
GROUP BY m.match_type;
""".strip(),
        "explanation": "MAX() per match_type group finds each format's individual record score.",
    },
    {
        "id": 8, "level": "Beginner",
        "title": "Series that started in 2024",
        "business_problem": "Archive page listing everything scheduled in a given year.",
        "concepts": "String/date filtering with strftime",
        "sql": """
SELECT series_name, host_country, match_type, start_date, total_matches
FROM series
WHERE strftime('%Y', start_date) = '2024'
ORDER BY start_date;
""".strip(),
        "explanation": "strftime('%Y', start_date) extracts the year component from a "
            "DATE column for comparison.",
    },

    # ------------------------------------------------------------------ #
    # INTERMEDIATE
    # ------------------------------------------------------------------ #
    {
        "id": 9, "level": "Intermediate",
        "title": "All-rounders: 1000+ runs and 50+ wickets",
        "business_problem": "Selectors want a shortlist of genuine all-rounders by career output.",
        "concepts": "CTEs, independent aggregation, HAVING",
        "sql": """
WITH bat_totals AS (
    SELECT player_id, SUM(runs_scored) AS total_runs
    FROM batting_scorecards GROUP BY player_id
),
bowl_totals AS (
    SELECT player_id, SUM(wickets_taken) AS total_wickets
    FROM bowling_scorecards GROUP BY player_id
),
formats AS (
    SELECT player_id, GROUP_CONCAT(DISTINCT match_type) AS formats_played FROM (
        SELECT b.player_id, m.match_type FROM batting_scorecards b JOIN matches m ON b.match_id = m.match_id
        UNION
        SELECT bo.player_id, m.match_type FROM bowling_scorecards bo JOIN matches m ON bo.match_id = m.match_id
    ) x GROUP BY player_id
)
SELECT p.full_name, bt.total_runs, bw.total_wickets, f.formats_played
FROM players p
JOIN bat_totals bt ON bt.player_id = p.player_id
JOIN bowl_totals bw ON bw.player_id = p.player_id
JOIN formats f ON f.player_id = p.player_id
WHERE p.playing_role = 'All-rounder'
  AND bt.total_runs > 1000 AND bw.total_wickets > 50
ORDER BY bt.total_runs DESC;
""".strip(),
        "explanation": "Runs and wickets are aggregated in *separate* CTEs (not one "
            "joined query) because joining batting-to-bowling rows directly would "
            "silently drop matches where a player only batted or only bowled, "
            "under-counting their totals.",
    },
    {
        "id": 10, "level": "Intermediate",
        "title": "Last 20 completed matches",
        "business_problem": "A 'recent results' ticker for the home page.",
        "concepts": "Multiple JOINs (including a self-referencing LEFT JOIN to teams)",
        "sql": """
SELECT
    m.match_description,
    t1.team_name AS team1,
    t2.team_name AS team2,
    tw.team_name AS winning_team,
    m.victory_margin,
    m.victory_type,
    v.venue_name
FROM matches m
JOIN teams t1       ON m.team1_id = t1.team_id
JOIN teams t2       ON m.team2_id = t2.team_id
LEFT JOIN teams tw  ON m.winner_team_id = tw.team_id
JOIN venues v       ON m.venue_id = v.venue_id
WHERE m.match_status = 'completed'
ORDER BY m.match_date DESC
LIMIT 20;
""".strip(),
        "explanation": "teams is joined three separate times with different aliases "
            "(team1, team2, winner) since a match references the same table in three roles.",
    },
    {
        "id": 11, "level": "Intermediate",
        "title": "Cross-format performance comparison",
        "business_problem": "Selectors comparing a player's Test/ODI/T20I output side by side.",
        "concepts": "CTE + conditional aggregation (pivoting rows into columns)",
        "sql": """
WITH per_format AS (
    SELECT b.player_id, m.match_type, SUM(b.runs_scored) AS runs,
           SUM(CASE WHEN b.dismissal_type <> 'not out' THEN 1 ELSE 0 END) AS outs
    FROM batting_scorecards b JOIN matches m ON b.match_id = m.match_id
    GROUP BY b.player_id, m.match_type
),
pivoted AS (
    SELECT player_id,
        SUM(CASE WHEN match_type = 'Test' THEN runs ELSE 0 END) AS test_runs,
        SUM(CASE WHEN match_type = 'ODI'  THEN runs ELSE 0 END) AS odi_runs,
        SUM(CASE WHEN match_type = 'T20I' THEN runs ELSE 0 END) AS t20i_runs,
        SUM(runs) AS total_runs, SUM(outs) AS total_outs,
        COUNT(DISTINCT match_type) AS formats_played
    FROM per_format GROUP BY player_id
)
SELECT p.full_name, pv.test_runs, pv.odi_runs, pv.t20i_runs,
       ROUND2(pv.total_runs * 1.0 / NULLIF(pv.total_outs, 0), 2) AS overall_batting_average
FROM pivoted pv JOIN players p ON p.player_id = pv.player_id
WHERE pv.formats_played >= 2
ORDER BY pv.total_runs DESC;
""".strip(),
        "explanation": "'Pivoting' with SUM(CASE WHEN ...) turns per-format rows into "
            "per-format columns -- SQLite has no native PIVOT keyword, so this pattern "
            "stands in for it.",
    },
    {
        "id": 12, "level": "Intermediate",
        "title": "Home vs away win analysis",
        "business_problem": "Team management wants to know if home advantage is real for their side.",
        "concepts": "Non-equi JOIN, conditional aggregation",
        "sql": """
WITH team_matches AS (
    SELECT m.match_id, m.winner_team_id, t.team_id, t.country AS team_country, v.country AS venue_country
    FROM matches m
    JOIN teams t  ON t.team_id IN (m.team1_id, m.team2_id)
    JOIN venues v ON v.venue_id = m.venue_id
    WHERE m.match_status = 'completed'
)
SELECT t2.team_name,
    SUM(CASE WHEN tm.team_country = tm.venue_country AND tm.winner_team_id = tm.team_id THEN 1 ELSE 0 END) AS home_wins,
    SUM(CASE WHEN tm.team_country <> tm.venue_country AND tm.winner_team_id = tm.team_id THEN 1 ELSE 0 END) AS away_wins,
    SUM(CASE WHEN tm.team_country = tm.venue_country THEN 1 ELSE 0 END) AS home_matches,
    SUM(CASE WHEN tm.team_country <> tm.venue_country THEN 1 ELSE 0 END) AS away_matches
FROM team_matches tm
JOIN teams t2 ON t2.team_id = tm.team_id
GROUP BY tm.team_id
ORDER BY (home_wins + away_wins) DESC;
""".strip(),
        "explanation": "The JOIN condition `t.team_id IN (m.team1_id, m.team2_id)` "
            "deliberately produces two rows per match -- one per participating team -- "
            "so each team's home/away status can be evaluated independently by "
            "comparing its country to the venue's country.",
    },
    {
        "id": 13, "level": "Intermediate",
        "title": "100+ run batting partnerships",
        "business_problem": "Highlight package: 'best partnerships of the season'.",
        "concepts": "Self-JOIN on adjacent batting positions",
        "sql": """
SELECT
    p1.full_name AS batsman1,
    p2.full_name AS batsman2,
    (b1.runs_scored + b2.runs_scored) AS partnership_runs,
    b1.innings_number
FROM batting_scorecards b1
JOIN batting_scorecards b2
    ON b1.match_id = b2.match_id
   AND b1.innings_number = b2.innings_number
   AND b1.team_id = b2.team_id
   AND b2.batting_position = b1.batting_position + 1
JOIN players p1 ON p1.player_id = b1.player_id
JOIN players p2 ON p2.player_id = b2.player_id
WHERE (b1.runs_scored + b2.runs_scored) >= 100
ORDER BY partnership_runs DESC;
""".strip(),
        "explanation": "A self-join on batting_scorecards pairs each batsman with the "
            "one at position+1 in the same match/innings/team -- the standard SQL "
            "pattern for 'compare a row to the next row'.",
    },
    {
        "id": 14, "level": "Intermediate",
        "title": "Bowling performance by venue",
        "business_problem": "Team analysts picking bowlers suited to an upcoming venue.",
        "concepts": "CTE pre-filtering, GROUP BY, HAVING",
        "sql": """
WITH filtered AS (
    SELECT bo.player_id, m.venue_id, bo.match_id, bo.overs_bowled, bo.runs_conceded, bo.wickets_taken
    FROM bowling_scorecards bo JOIN matches m ON bo.match_id = m.match_id
    WHERE bo.overs_bowled >= 4
),
agg AS (
    SELECT player_id, venue_id,
           COUNT(DISTINCT match_id) AS matches_at_venue,
           SUM(wickets_taken) AS total_wickets,
           ROUND2(SUM(runs_conceded) * 1.0 / NULLIF(SUM(overs_bowled), 0), 2) AS avg_economy
    FROM filtered GROUP BY player_id, venue_id
)
SELECT p.full_name, v.venue_name, a.matches_at_venue, a.total_wickets, a.avg_economy
FROM agg a
JOIN players p ON p.player_id = a.player_id
JOIN venues v  ON v.venue_id = a.venue_id
WHERE a.matches_at_venue >= 3
ORDER BY a.avg_economy ASC;
""".strip(),
        "explanation": "The 'bowled at least 4 overs' rule is applied first (WHERE, "
            "row-level), then the 'at least 3 matches at the venue' rule is applied "
            "after aggregation -- row filters and group filters are deliberately kept "
            "in the right order.",
    },
    {
        "id": 15, "level": "Intermediate",
        "title": "Performance in close matches",
        "business_problem": "Identify clutch players for high-pressure run-chases.",
        "concepts": "CTE, conditional aggregation, business-rule filtering",
        "sql": """
WITH close_matches AS (
    SELECT match_id, winner_team_id FROM matches
    WHERE match_status = 'completed' AND (
        (victory_type = 'runs'    AND victory_margin < 50) OR
        (victory_type = 'wickets' AND victory_margin < 5)
    )
),
player_close AS (
    SELECT b.player_id, b.team_id, b.match_id, b.runs_scored, cm.winner_team_id
    FROM batting_scorecards b JOIN close_matches cm ON b.match_id = cm.match_id
)
SELECT p.full_name,
    ROUND2(AVG(pc.runs_scored), 2) AS avg_runs_close_matches,
    COUNT(DISTINCT pc.match_id) AS close_matches_played,
    SUM(CASE WHEN pc.team_id = pc.winner_team_id THEN 1 ELSE 0 END) AS close_matches_won_when_batted
FROM player_close pc JOIN players p ON p.player_id = pc.player_id
GROUP BY pc.player_id
ORDER BY avg_runs_close_matches DESC;
""".strip(),
        "explanation": "'Close match' is defined once in a CTE so the business rule "
            "lives in a single place, then every player's batting rows from those "
            "matches are pulled and aggregated.",
    },
    {
        "id": 16, "level": "Intermediate",
        "title": "Year-over-year batting trend since 2020",
        "business_problem": "Track a player's form arc season by season.",
        "concepts": "Date functions, GROUP BY with HAVING",
        "sql": """
SELECT p.full_name, strftime('%Y', m.match_date) AS year,
    ROUND2(AVG(b.runs_scored), 2) AS avg_runs_per_match,
    ROUND2(AVG(CASE WHEN b.balls_faced > 0 THEN b.runs_scored * 100.0 / b.balls_faced END), 2) AS avg_strike_rate,
    COUNT(DISTINCT b.match_id) AS matches_played
FROM batting_scorecards b
JOIN matches m  ON b.match_id = m.match_id
JOIN players p  ON p.player_id = b.player_id
WHERE m.match_date >= '2020-01-01'
GROUP BY b.player_id, year
HAVING COUNT(DISTINCT b.match_id) >= 5
ORDER BY p.full_name, year;
""".strip(),
        "explanation": "GROUP BY player AND year produces one row per player per "
            "season; HAVING filters out player-years with too little sample size "
            "(fewer than 5 matches) to be meaningful.",
    },

    # ------------------------------------------------------------------ #
    # ADVANCED
    # ------------------------------------------------------------------ #
    {
        "id": 17, "level": "Advanced",
        "title": "Does winning the toss matter?",
        "business_problem": "Commentary talking point: quantify the toss advantage.",
        "concepts": "Conditional aggregation, percentage calculation",
        "sql": """
SELECT toss_decision,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN toss_winner_id = winner_team_id THEN 1 ELSE 0 END) AS toss_winner_also_won,
    ROUND2(SUM(CASE WHEN toss_winner_id = winner_team_id THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_pct
FROM matches
WHERE match_status = 'completed' AND toss_decision IS NOT NULL
GROUP BY toss_decision;
""".strip(),
        "explanation": "Groups completed matches by the toss-winner's decision (bat "
            "or bowl first) and computes what fraction of the time the toss winner "
            "also won the match.",
    },
    {
        "id": 18, "level": "Advanced",
        "title": "Most economical limited-overs bowlers",
        "business_problem": "Fantasy platforms ranking bowlers by run-saving efficiency.",
        "concepts": "CTE, HAVING on multiple derived conditions",
        "sql": """
WITH bowler_matches AS (
    SELECT bo.player_id, bo.match_id, bo.overs_bowled, bo.runs_conceded, bo.wickets_taken
    FROM bowling_scorecards bo JOIN matches m ON bo.match_id = m.match_id
    WHERE m.match_type IN ('ODI', 'T20I')
),
agg AS (
    SELECT player_id,
        COUNT(DISTINCT match_id) AS matches_played,
        SUM(overs_bowled) AS total_overs,
        SUM(runs_conceded) AS total_runs,
        SUM(wickets_taken) AS total_wickets,
        AVG(overs_bowled) AS avg_overs_per_match
    FROM bowler_matches GROUP BY player_id
)
SELECT p.full_name,
    ROUND2(a.total_runs * 1.0 / NULLIF(a.total_overs, 0), 2) AS economy_rate,
    a.total_wickets, a.matches_played
FROM agg a JOIN players p ON p.player_id = a.player_id
WHERE a.matches_played >= 10 AND a.avg_overs_per_match >= 2
ORDER BY economy_rate ASC
LIMIT 25;
""".strip(),
        "explanation": "Both eligibility rules (>=10 matches, >=2 overs/match on "
            "average) are applied on the aggregated CTE, then economy rate is "
            "computed and sorted ascending (lower is better).",
    },
    {
        "id": 19, "level": "Advanced",
        "title": "Most consistent batsmen (lowest std. deviation)",
        "business_problem": "Team management prefers reliable scorers over boom-or-bust ones.",
        "concepts": "Custom STDEV() aggregate, CTE, HAVING",
        "sql": """
WITH innings AS (
    SELECT b.player_id, b.runs_scored, b.balls_faced
    FROM batting_scorecards b JOIN matches m ON b.match_id = m.match_id
    WHERE b.balls_faced >= 10 AND m.match_date >= '2022-01-01'
)
SELECT p.full_name,
    ROUND2(AVG(i.runs_scored), 2) AS avg_runs,
    ROUND2(STDEV(i.runs_scored), 2) AS stdev_runs,
    COUNT(*) AS innings_played
FROM innings i JOIN players p ON p.player_id = i.player_id
GROUP BY i.player_id
HAVING COUNT(*) >= 5
ORDER BY stdev_runs ASC;
""".strip(),
        "explanation": "SQLite has no built-in STDEV -- utils/db_connection.py "
            "registers a custom aggregate function that computes population standard "
            "deviation, used here exactly like any built-in aggregate. A lower value "
            "means more consistent scoring.",
    },
    {
        "id": 20, "level": "Advanced",
        "title": "Cross-format match count and averages (20+ total matches)",
        "business_problem": "Identify genuinely multi-format players for workload planning.",
        "concepts": "CTE pivoting, multi-condition filtering via a totals CTE",
        "sql": """
WITH per_format AS (
    SELECT b.player_id, m.match_type,
        COUNT(DISTINCT b.match_id) AS matches_in_format,
        SUM(b.runs_scored) AS runs,
        SUM(CASE WHEN b.dismissal_type <> 'not out' THEN 1 ELSE 0 END) AS outs
    FROM batting_scorecards b JOIN matches m ON b.match_id = m.match_id
    GROUP BY b.player_id, m.match_type
),
totals AS (
    SELECT player_id, SUM(matches_in_format) AS total_matches FROM per_format GROUP BY player_id
)
SELECT p.full_name,
    SUM(CASE WHEN pf.match_type = 'Test' THEN pf.matches_in_format ELSE 0 END) AS test_matches,
    ROUND2(SUM(CASE WHEN pf.match_type = 'Test' THEN pf.runs ELSE 0 END) * 1.0 /
        NULLIF(SUM(CASE WHEN pf.match_type = 'Test' THEN pf.outs ELSE 0 END), 0), 2) AS test_avg,
    SUM(CASE WHEN pf.match_type = 'ODI' THEN pf.matches_in_format ELSE 0 END) AS odi_matches,
    ROUND2(SUM(CASE WHEN pf.match_type = 'ODI' THEN pf.runs ELSE 0 END) * 1.0 /
        NULLIF(SUM(CASE WHEN pf.match_type = 'ODI' THEN pf.outs ELSE 0 END), 0), 2) AS odi_avg,
    SUM(CASE WHEN pf.match_type = 'T20I' THEN pf.matches_in_format ELSE 0 END) AS t20i_matches,
    ROUND2(SUM(CASE WHEN pf.match_type = 'T20I' THEN pf.runs ELSE 0 END) * 1.0 /
        NULLIF(SUM(CASE WHEN pf.match_type = 'T20I' THEN pf.outs ELSE 0 END), 0), 2) AS t20i_avg
FROM per_format pf
JOIN players p  ON p.player_id = pf.player_id
JOIN totals t   ON t.player_id = pf.player_id
WHERE t.total_matches >= 20
GROUP BY pf.player_id
ORDER BY (test_matches + odi_matches + t20i_matches) DESC;
""".strip(),
        "explanation": "A separate `totals` CTE computes the career match count so "
            "the >=20 filter can be applied in the outer WHERE without breaking the "
            "per-format GROUP BY in the main SELECT.",
    },
    {
        "id": 21, "level": "Advanced",
        "title": "Weighted composite performance ranking",
        "business_problem": "A single 'best all-round performer' leaderboard combining bat/bowl/field.",
        "concepts": "Multiple CTEs, weighted scoring formula, RANK() window function",
        "sql": """
WITH bat_stats AS (
    SELECT b.player_id, m.match_type,
        SUM(b.runs_scored) AS runs,
        SUM(CASE WHEN b.dismissal_type <> 'not out' THEN 1 ELSE 0 END) AS outs,
        SUM(b.balls_faced) AS balls
    FROM batting_scorecards b JOIN matches m ON b.match_id = m.match_id
    GROUP BY b.player_id, m.match_type
),
bowl_stats AS (
    SELECT bo.player_id, m.match_type,
        SUM(bo.wickets_taken) AS wickets,
        SUM(bo.runs_conceded) AS runs_conceded,
        SUM(bo.overs_bowled) AS overs
    FROM bowling_scorecards bo JOIN matches m ON bo.match_id = m.match_id
    GROUP BY bo.player_id, m.match_type
),
field_stats AS (
    SELECT f.player_id, m.match_type,
        SUM(f.catches) AS catches, SUM(f.stumpings) AS stumpings
    FROM fielding_scorecards f JOIN matches m ON f.match_id = m.match_id
    GROUP BY f.player_id, m.match_type
),
combined AS (
    SELECT bs.player_id, bs.match_type,
        bs.runs,
        bs.runs * 1.0 / NULLIF(bs.outs, 0) AS batting_average,
        bs.runs * 100.0 / NULLIF(bs.balls, 0) AS strike_rate,
        COALESCE(bw.wickets, 0) AS wickets,
        COALESCE(bw.runs_conceded, 0) * 1.0 / NULLIF(bw.overs, 0) AS bowling_average_proxy,
        COALESCE(bw.runs_conceded, 0) * 1.0 / NULLIF(bw.overs, 0) AS economy_rate,
        COALESCE(fs.catches, 0) AS catches, COALESCE(fs.stumpings, 0) AS stumpings
    FROM bat_stats bs
    LEFT JOIN bowl_stats bw  ON bw.player_id = bs.player_id AND bw.match_type = bs.match_type
    LEFT JOIN field_stats fs ON fs.player_id = bs.player_id AND fs.match_type = bs.match_type
),
scored AS (
    SELECT player_id, match_type,
        (COALESCE(runs, 0) * 0.01 + COALESCE(batting_average, 0) * 0.5 + COALESCE(strike_rate, 0) * 0.3) AS batting_points,
        (COALESCE(wickets, 0) * 2 + (50 - COALESCE(bowling_average_proxy, 50)) * 0.5 + (6 - COALESCE(economy_rate, 6)) * 2) AS bowling_points,
        (COALESCE(catches, 0) * 3 + COALESCE(stumpings, 0) * 5) AS fielding_points
    FROM combined
)
SELECT * FROM (
    SELECT p.full_name, s.match_type,
        ROUND2(s.batting_points, 2) AS batting_points,
        ROUND2(s.bowling_points, 2) AS bowling_points,
        ROUND2(s.fielding_points, 2) AS fielding_points,
        ROUND2(s.batting_points + s.bowling_points + s.fielding_points, 2) AS total_score,
        RANK() OVER (PARTITION BY s.match_type ORDER BY (s.batting_points + s.bowling_points + s.fielding_points) DESC) AS format_rank
    FROM scored s JOIN players p ON p.player_id = s.player_id
) ranked
WHERE format_rank <= 10
ORDER BY match_type, format_rank;
""".strip(),
        "explanation": "Three independent CTEs compute batting/bowling/fielding "
            "aggregates per player per format, a fourth applies the given weighted "
            "formula, and RANK() OVER (PARTITION BY match_type ...) ranks players "
            "separately within each format -- exactly what 'rank top performers in "
            "each format' requires.",
    },
    {
        "id": 22, "level": "Advanced",
        "title": "Head-to-head team analysis (last 3 years)",
        "business_problem": "Prediction models need historical head-to-head baselines.",
        "concepts": "Canonical pair ordering, CTEs, conditional aggregation",
        "sql": """
WITH h2h AS (
    SELECT match_id, team1_id, team2_id, winner_team_id, victory_margin, victory_type
    FROM matches
    WHERE match_status = 'completed' AND match_date >= date('now', '-3 years')
),
pairs AS (
    SELECT
        CASE WHEN team1_id < team2_id THEN team1_id ELSE team2_id END AS team_a,
        CASE WHEN team1_id < team2_id THEN team2_id ELSE team1_id END AS team_b,
        winner_team_id, victory_margin, victory_type
    FROM h2h
)
SELECT ta.team_name AS team_a, tb.team_name AS team_b,
    COUNT(*) AS total_matches,
    SUM(CASE WHEN winner_team_id = p.team_a THEN 1 ELSE 0 END) AS team_a_wins,
    SUM(CASE WHEN winner_team_id = p.team_b THEN 1 ELSE 0 END) AS team_b_wins,
    ROUND2(AVG(CASE WHEN victory_type = 'runs' THEN victory_margin END), 2) AS avg_margin_runs,
    ROUND2(AVG(CASE WHEN victory_type = 'wickets' THEN victory_margin END), 2) AS avg_margin_wickets,
    ROUND2(SUM(CASE WHEN winner_team_id = p.team_a THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS team_a_win_pct
FROM pairs p
JOIN teams ta ON ta.team_id = p.team_a
JOIN teams tb ON tb.team_id = p.team_b
GROUP BY p.team_a, p.team_b
HAVING COUNT(*) >= 5
ORDER BY total_matches DESC;
""".strip(),
        "explanation": "Because 'India vs Australia' and 'Australia vs India' should "
            "be the same pair, `pairs` normalizes team1/team2 into a canonical "
            "team_a < team_b ordering before grouping -- otherwise the same rivalry "
            "would be split into two rows depending on who's listed first.",
    },
    {
        "id": 23, "level": "Advanced",
        "title": "Recent form and momentum (last 10 innings)",
        "business_problem": "Fantasy captains need 'who's in form right now'.",
        "concepts": "ROW_NUMBER() window function, custom STDEV, CASE-based classification",
        "sql": """
WITH recent AS (
    SELECT b.player_id, b.runs_scored, b.balls_faced, m.match_date,
        ROW_NUMBER() OVER (PARTITION BY b.player_id ORDER BY m.match_date DESC) AS rn
    FROM batting_scorecards b JOIN matches m ON b.match_id = m.match_id
    WHERE m.match_status = 'completed'
),
last10 AS (SELECT * FROM recent WHERE rn <= 10)
SELECT p.full_name,
    ROUND2(AVG(CASE WHEN rn <= 5 THEN runs_scored END), 2) AS avg_runs_last5,
    ROUND2(AVG(runs_scored), 2) AS avg_runs_last10,
    ROUND2(AVG(CASE WHEN balls_faced > 0 THEN runs_scored * 100.0 / balls_faced END), 2) AS avg_strike_rate_last10,
    SUM(CASE WHEN runs_scored >= 50 THEN 1 ELSE 0 END) AS scores_above_50,
    ROUND2(STDEV(runs_scored), 2) AS consistency_stdev,
    CASE
        WHEN AVG(runs_scored) >= 45 AND SUM(CASE WHEN runs_scored >= 50 THEN 1 ELSE 0 END) >= 3 THEN 'Excellent Form'
        WHEN AVG(runs_scored) >= 30 THEN 'Good Form'
        WHEN AVG(runs_scored) >= 15 THEN 'Average Form'
        ELSE 'Poor Form'
    END AS form_category
FROM last10 l JOIN players p ON p.player_id = l.player_id
GROUP BY l.player_id
HAVING COUNT(*) >= 10
ORDER BY avg_runs_last10 DESC;
""".strip(),
        "explanation": "ROW_NUMBER() PARTITION BY player ORDER BY date DESC labels "
            "each player's innings 1 (most recent) through N -- filtering rn<=10 "
            "gives 'last 10 innings' per player without a correlated subquery.",
    },
    {
        "id": 24, "level": "Advanced",
        "title": "Best batting partnership combinations",
        "business_problem": "Coaches deciding a settled batting order based on proven pairings.",
        "concepts": "Self-JOIN + CTE + success-rate calculation",
        "sql": """
WITH partnerships AS (
    SELECT b1.player_id AS p1, b2.player_id AS p2,
        (b1.runs_scored + b2.runs_scored) AS partnership_runs
    FROM batting_scorecards b1
    JOIN batting_scorecards b2
        ON b1.match_id = b2.match_id
       AND b1.innings_number = b2.innings_number
       AND b1.team_id = b2.team_id
       AND b2.batting_position = b1.batting_position + 1
),
agg AS (
    SELECT p1, p2, COUNT(*) AS partnerships_count,
        ROUND2(AVG(partnership_runs), 2) AS avg_partnership_runs,
        SUM(CASE WHEN partnership_runs > 50 THEN 1 ELSE 0 END) AS partnerships_above_50,
        MAX(partnership_runs) AS highest_partnership
    FROM partnerships GROUP BY p1, p2
)
SELECT pl1.full_name AS batsman1, pl2.full_name AS batsman2,
    a.partnerships_count, a.avg_partnership_runs, a.partnerships_above_50, a.highest_partnership,
    ROUND2(a.partnerships_above_50 * 100.0 / a.partnerships_count, 2) AS success_rate_pct
FROM agg a
JOIN players pl1 ON pl1.player_id = a.p1
JOIN players pl2 ON pl2.player_id = a.p2
WHERE a.partnerships_count >= 5
ORDER BY success_rate_pct DESC, a.avg_partnership_runs DESC;
""".strip(),
        "explanation": "Reuses the same adjacent-position self-join as Q13, but "
            "aggregates by the (player1, player2) pair instead of listing individual "
            "partnerships, then derives a success rate from the >50-run count.",
    },
    {
        "id": 25, "level": "Advanced",
        "title": "Career trajectory: quarterly time-series analysis",
        "business_problem": "Is a player trending up, down, or steady over their career?",
        "concepts": "Quarter bucketing, window functions (ROW_NUMBER, COUNT OVER), phase classification",
        "sql": """
WITH quarterly AS (
    SELECT b.player_id,
        strftime('%Y', m.match_date) || '-Q' ||
            ((CAST(strftime('%m', m.match_date) AS INTEGER) - 1) / 3 + 1) AS quarter,
        m.match_date, b.runs_scored, b.balls_faced
    FROM batting_scorecards b JOIN matches m ON b.match_id = m.match_id
    WHERE m.match_status = 'completed'
),
qagg AS (
    SELECT player_id, quarter, MIN(match_date) AS quarter_start,
        COUNT(*) AS matches_in_quarter, AVG(runs_scored) AS avg_runs
    FROM quarterly GROUP BY player_id, quarter
    HAVING COUNT(*) >= 3
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY quarter_start) AS rn,
        COUNT(*) OVER (PARTITION BY player_id) AS total_q
    FROM qagg
),
halves AS (
    SELECT player_id, total_q,
        AVG(CASE WHEN rn <= total_q / 2 THEN avg_runs END) AS early_career_avg_runs,
        AVG(CASE WHEN rn >  total_q / 2 THEN avg_runs END) AS recent_career_avg_runs
    FROM ranked GROUP BY player_id
)
SELECT p.full_name, h.total_q AS quarters_active,
    ROUND2(h.early_career_avg_runs, 2) AS early_career_avg_runs,
    ROUND2(h.recent_career_avg_runs, 2) AS recent_career_avg_runs,
    CASE
        WHEN h.recent_career_avg_runs > h.early_career_avg_runs * 1.1 THEN 'Career Ascending'
        WHEN h.recent_career_avg_runs < h.early_career_avg_runs * 0.9 THEN 'Career Declining'
        ELSE 'Career Stable'
    END AS career_phase
FROM halves h JOIN players p ON p.player_id = h.player_id
WHERE h.total_q >= 6
ORDER BY recent_career_avg_runs DESC;
""".strip(),
        "explanation": "Matches are bucketed into calendar quarters, quarters with "
            "too few matches are dropped, then ROW_NUMBER()+COUNT() OVER a player "
            "partition splits each player's timeline into an early half and a recent "
            "half so the two can be compared to classify career direction.",
    },
]

LEVELS = ["Beginner", "Intermediate", "Advanced"]


def get_query(qid: int):
    for q in QUERIES:
        if q["id"] == qid:
            return q
    return None
