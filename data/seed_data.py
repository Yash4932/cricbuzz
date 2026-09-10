"""
data/seed_data.py
------------------
Generates a realistic, internally-consistent synthetic cricket dataset and
loads it into the configured database (SQLite by default).

Why synthetic data at all, given this is an "API integration" project?
The Cricbuzz API only exposes *current* live/recent data -- it has no
endpoint for "give me 6 years of ball-by-ball history for 150 players",
which is exactly what the 25 SQL analytics questions need (year-over-year
trends, quarterly form, head-to-head over 3 years, etc). So the standard
approach (and what the reference project does) is: use the live API for
the Live Matches / Top Stats pages, and maintain a separately-seeded
historical warehouse for the analytics + CRUD pages. This script builds
that warehouse.

Run directly:  python data/seed_data.py
"""

import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config
from utils.db_connection import get_connection, run_script

random.seed(42)

TODAY = date(2026, 9, 3)

TEAMS = [
    ("India", "India"), ("Australia", "Australia"), ("England", "England"),
    ("South Africa", "South Africa"), ("New Zealand", "New Zealand"),
    ("Pakistan", "Pakistan"), ("Sri Lanka", "Sri Lanka"), ("Bangladesh", "Bangladesh"),
    ("West Indies", "West Indies"), ("Afghanistan", "Afghanistan"),
    ("Zimbabwe", "Zimbabwe"), ("Ireland", "Ireland"),
]

# ---------------------------------------------------------------------------
# Per-country name pools. Deliberately kept SEPARATE per country (rather than
# one shared flat list) so a player's first and last name always sound like
# they belong to the same nationality -- an earlier version of this script
# drew first/last names from one global pool and produced nonsense like
# "Steve Bumrah" or "Jasprit Labuschagne". First/last names within a pool are
# also intentionally offset when paired (see gen_players) so common real
# player full-name combinations aren't reproduced verbatim.
# ---------------------------------------------------------------------------
NAME_POOLS = {
    "India": (
        ["Arjun", "Vikram", "Rohan", "Aditya", "Karan", "Nikhil", "Suresh", "Aakash",
         "Devansh", "Manish", "Rajat", "Sourav", "Yuvan", "Pranav"],
        ["Rathore", "Verma", "Nair", "Chauhan", "Deshmukh", "Bhatt", "Kapoor", "Menon",
         "Solanki", "Iyer", "Trivedi", "Choudhury", "Malhotra", "Saxena"],
    ),
    "Australia": (
        ["Blake", "Ryan", "Connor", "Liam", "Nathan", "Ethan", "Cody", "Dean",
         "Shane", "Brendon", "Callum", "Jarrod", "Reece", "Aaron"],
        ["Whittaker", "Pearson", "Fletcher", "Donnelly", "Sinclair", "Marsh", "Kingsley",
         "Harmon", "Prescott", "Doyle", "Blackwood", "Sutton", "Grady", "Nolan"],
    ),
    "England": (
        ["Oliver", "George", "Freddie", "Callum", "Jamie", "Charlie", "Alfie", "Toby",
         "Louis", "Archie", "Ollie", "Max", "Reuben", "Finlay"],
        ["Ashworth", "Pemberton", "Whitfield", "Carrington", "Hargreaves", "Sutcliffe",
         "Fenwick", "Marlowe", "Beaumont", "Winstone", "Radcliffe", "Ellery", "Thackeray", "Osborne"],
    ),
    "South Africa": (
        ["Werner", "Dewald", "Marco", "Ruan", "Heinrich", "Christiaan", "Stefan", "Bjorn",
         "Deon", "Andre", "Pieter", "Riaan", "Johan", "Cobus"],
        ["van Wyk", "Botha", "Steyn", "Coetzee", "Pretorius", "du Preez", "Kruger",
         "Fourie", "Venter", "Nel", "Marais", "Erasmus", "Viljoen", "Swanepoel"],
    ),
    "New Zealand": (
        ["Logan", "Finn", "Cameron", "Jesse", "Corey", "Hamish", "Zane", "Lachlan",
         "Riley", "Mason", "Brayden", "Tyler", "Jordy", "Scott"],
        ["MacKenzie", "Fraser", "Bell", "Harrow", "Dawson", "Grierson", "Anderson",
         "Whitmore", "Calder", "Sinclair", "Duncan", "Aitken", "Lockhart", "Broughton"],
    ),
    "Pakistan": (
        ["Usman", "Bilal", "Hamza", "Owais", "Kashif", "Adnan", "Faisal", "Sami",
         "Zeeshan", "Umair", "Waqas", "Junaid", "Arsalan", "Talha"],
        ["Bhatti", "Chaudhry", "Malik", "Qureshi", "Siddiqui", "Farooq", "Sheikh",
         "Baig", "Raza", "Iqbal", "Aslam", "Javed", "Latif", "Mirza"],
    ),
    "Sri Lanka": (
        ["Nuwan", "Chamara", "Ruwan", "Sanath", "Isuru", "Lahiru", "Buddhika", "Malinda",
         "Sachith", "Dulan", "Ashan", "Chathura", "Kavindu", "Tharindu"],
        ["Perera", "Fernando", "Gunawardena", "Jayasuriya", "Rajapaksa", "Wickramasinghe",
         "Bandara", "Dissanayake", "Weerasinghe", "Ratnayake", "Abeysekera", "Senanayake",
         "Kariyawasam", "Wijesinghe"],
    ),
    "Bangladesh": (
        ["Rakib", "Sabbir", "Nasir", "Arafat", "Sohel", "Emran", "Rubel", "Tanvir",
         "Jahid", "Foysal", "Rayhan", "Sajid", "Milon", "Kamrul"],
        ["Chowdhury", "Ahmed", "Karim", "Uddin", "Miah", "Talukder", "Sarkar",
         "Mollah", "Molla", "Khandaker", "Bhuiyan", "Akhtar", "Siddique", "Rana"],
    ),
    "West Indies": (
        ["Marlon", "Andre", "Kevron", "Jerome", "Sherwin", "Delano", "Tremayne", "Odean",
         "Keon", "Rahkeem", "Sheldon", "Denesh", "Akeal", "Raymon"],
        ["Baptiste", "Ferguson", "Simmonds", "Charles", "Alleyne", "Greaves", "Sealy",
         "Browne", "Layne", "Weekes", "Marshall", "Griffith", "Forde", "Skeete"],
    ),
    "Afghanistan": (
        ["Karim", "Zubair", "Farhan", "Waheed", "Jamshid", "Sultan", "Bashir", "Nawid",
         "Sediq", "Yosuf", "Hamidullah", "Tariq", "Ehsan", "Latif"],
        ["Stanikzai", "Popal", "Sharafi", "Wardak", "Rahimi", "Achakzai", "Amiri",
         "Noori", "Sadiqi", "Rasooli", "Karimi", "Barakzai", "Hotak", "Andar"],
    ),
    "Zimbabwe": (
        ["Tinashe", "Blessing", "Takudzwa", "Munashe", "Kudakwashe", "Tapiwa", "Farai",
         "Simba", "Tendai", "Wellington", "Elton", "Brendan", "Craig", "Donald"],
        ["Chikwanha", "Muzarabani", "Mavuta", "Mutandwa", "Chigumira", "Masakadza",
         "Mupariwa", "Ndlovu", "Chibhabha", "Gwande", "Mutasa", "Musakanda", "Chatara", "Zvarevashe"],
    ),
    "Ireland": (
        ["Cian", "Declan", "Ronan", "Eoin", "Aidan", "Fintan", "Barry", "Niall",
         "Shane", "Cormac", "Darragh", "Conor", "Padraig", "Rory"],
        ["Delaney", "Gallagher", "Fitzgerald", "Kavanagh", "Brennan", "Whelan",
         "McCarthy", "Doyle", "Hogan", "Costello", "Lynch", "Nolan", "Ryan", "Dunphy"],
    ),
}

ROLES = ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"]
ROLE_WEIGHTS = [0.38, 0.34, 0.20, 0.08]
BAT_STYLES = ["Right-hand bat", "Left-hand bat"]
BOWL_STYLES = [
    "Right-arm fast", "Right-arm fast-medium", "Left-arm fast",
    "Right-arm off break", "Left-arm orthodox", "Legbreak googly", None,
]

VENUES = [
    ("Melbourne Cricket Ground", "Melbourne", "Australia", 100024),
    ("Eden Gardens", "Kolkata", "India", 68000),
    ("Narendra Modi Stadium", "Ahmedabad", "India", 132000),
    ("Lord's", "London", "England", 30000),
    ("The Oval", "London", "England", 25500),
    ("Wankhede Stadium", "Mumbai", "India", 33000),
    ("Sydney Cricket Ground", "Sydney", "Australia", 48000),
    ("Newlands", "Cape Town", "South Africa", 25000),
    ("Wanderers Stadium", "Johannesburg", "South Africa", 34000),
    ("Basin Reserve", "Wellington", "New Zealand", 11600),
    ("Gaddafi Stadium", "Lahore", "Pakistan", 27000),
    ("R Premadasa Stadium", "Colombo", "Sri Lanka", 35000),
    ("Sher-e-Bangla Stadium", "Dhaka", "Bangladesh", 26000),
    ("Kensington Oval", "Bridgetown", "West Indies", 28000),
    ("M. Chinnaswamy Stadium", "Bengaluru", "India", 40000),
    ("Adelaide Oval", "Adelaide", "Australia", 53500),
    ("Old Trafford", "Manchester", "England", 26000),
    ("Trent Bridge", "Nottingham", "England", 17500),
    ("Rawalpindi Cricket Stadium", "Rawalpindi", "Pakistan", 15000),
    ("Optus Stadium", "Perth", "Australia", 61266),
]

FORMATS = ["Test", "ODI", "T20I"]
FORMAT_WEIGHTS = [0.28, 0.40, 0.32]


def gen_players(teams):
    players = []
    used_names = set()
    for team_id, (team_name, country) in teams.items():
        first_pool, last_pool = NAME_POOLS[country]
        n_players = random.randint(16, 20)
        for _ in range(n_players):
            for _try in range(30):
                name = f"{random.choice(first_pool)} {random.choice(last_pool)}"
                if name not in used_names:
                    used_names.add(name)
                    break
            role = random.choices(ROLES, weights=ROLE_WEIGHTS, k=1)[0]
            bat_style = random.choice(BAT_STYLES)
            bowl_style = None if role == "Batsman" else random.choice(BOWL_STYLES)
            if role == "Wicket-keeper":
                bowl_style = None
            dob = TODAY - timedelta(days=random.randint(20 * 365, 38 * 365))
            players.append({
                "full_name": name, "country": country, "playing_role": role,
                "batting_style": bat_style, "bowling_style": bowl_style,
                "date_of_birth": dob.isoformat(), "team_id": team_id,
            })
    return players


def random_date_weighted():
    """Bias dates so recent years (2023-2026) are denser, matching a live app."""
    start = date(2019, 1, 1)
    span_days = (TODAY - start).days
    # weight recent dates higher using a squared random draw
    r = random.random() ** 0.55
    offset = int(r * span_days)
    return start + timedelta(days=offset)


def build_scorecards(match, team1_roster, team2_roster, cur):
    match_id = match["match_id"]
    match_type = match["match_type"]
    innings_map = {1: (match["team1_id"], team1_roster), 2: (match["team2_id"], team2_roster)}
    if match_type == "Test":
        innings_map[3] = (match["team1_id"], team1_roster)
        innings_map[4] = (match["team2_id"], team2_roster)

    format_run_profile = {
        "Test": (35, 30, 130), "ODI": (32, 45, 110), "T20I": (22, 16, 145),
    }
    mean_runs, sd_runs, mean_sr = format_run_profile[match_type]

    all_bat_rows, all_bowl_rows, all_field_rows = [], [], []
    fielding_tally = {}

    for innings_no, (team_id, roster) in innings_map.items():
        batters = random.sample(roster, k=min(11, len(roster)))
        for pos, player_id in enumerate(batters, start=1):
            skill = random.uniform(0.6, 1.5)
            runs = max(0, int(random.gauss(mean_runs * skill * (1.15 if pos <= 4 else 0.7), sd_runs)))
            balls = max(runs // 2, int(runs / max(0.4, random.gauss(mean_sr, 25)) * 100)) if runs > 0 else random.randint(0, 8)
            balls = max(balls, 1 if runs == 0 else balls)
            fours = min(runs // 4, random.randint(0, max(1, runs // 6)))
            sixes = random.randint(0, max(0, runs // 20))
            dismissal = random.choice(["caught", "bowled", "lbw", "run out", "stumped", "not out"])
            all_bat_rows.append((match_id, innings_no, player_id, team_id, pos, runs, balls, fours, sixes, dismissal))

        bowl_team_id = innings_map[2][0] if team_id == innings_map[1][0] else innings_map[1][0]
        bowl_roster = team2_roster if team_id == innings_map[1][0] else team1_roster
        bowlers = random.sample(bowl_roster, k=min(6, len(bowl_roster)))
        max_overs = 90 / 6 if match_type == "Test" else (10 if match_type == "ODI" else 4)
        for player_id in bowlers:
            overs = round(random.uniform(max_overs * 0.4, max_overs), 1)
            econ = max(1.5, random.gauss(3.4 if match_type == "Test" else (5.2 if match_type == "ODI" else 7.8), 1.4))
            runs_conceded = max(0, int(overs * econ))
            wkts_lambda = 2.2 if match_type != "Test" else 1.9
            wickets = min(10, max(0, int(random.gauss(wkts_lambda, 1.6))))
            all_bowl_rows.append((match_id, innings_no, player_id, bowl_team_id, overs, runs_conceded, wickets))

        # fielding: assign catches/stumpings to a few bowl-side players
        for player_id in random.sample(bowl_roster, k=min(4, len(bowl_roster))):
            key = (player_id, bowl_team_id)
            catches = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
            stump = 0
            fielding_tally.setdefault(key, [0, 0])
            fielding_tally[key][0] += catches
            fielding_tally[key][1] += stump

    cur.executemany(
        """INSERT INTO batting_scorecards
           (match_id, innings_number, player_id, team_id, batting_position,
            runs_scored, balls_faced, fours, sixes, dismissal_type)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        all_bat_rows,
    )
    cur.executemany(
        """INSERT INTO bowling_scorecards
           (match_id, innings_number, player_id, team_id, overs_bowled, runs_conceded, wickets_taken)
           VALUES (?,?,?,?,?,?,?)""",
        all_bowl_rows,
    )
    field_rows = [(match_id, pid, tid, c, s) for (pid, tid), (c, s) in fielding_tally.items()]
    cur.executemany(
        """INSERT INTO fielding_scorecards (match_id, player_id, team_id, catches, stumpings)
           VALUES (?,?,?,?,?)""",
        field_rows,
    )


def main():
    schema_sql = (Path(__file__).resolve().parent.parent / "database" / "schema.sql").read_text()
    print(f"Resetting schema on {config.DB_ENGINE} ...")
    run_script(schema_sql)

    conn = get_connection()
    cur = conn.cursor()

    # --- Teams ---
    team_ids = {}
    for name, country in TEAMS:
        cur.execute("INSERT INTO teams (team_name, country) VALUES (?, ?)", (name, country))
        team_ids[name] = cur.lastrowid
    teams_by_id = {tid: (name, country) for name, tid in [(n, team_ids[n]) for n, _ in TEAMS]}
    teams_by_id = {team_ids[n]: (n, c) for n, c in TEAMS}

    # --- Venues ---
    venue_ids = []
    for vname, city, country, cap in VENUES:
        cur.execute(
            "INSERT INTO venues (venue_name, city, country, capacity) VALUES (?,?,?,?)",
            (vname, city, country, cap),
        )
        venue_ids.append(cur.lastrowid)

    # --- Players ---
    players_by_team = {tid: [] for tid in team_ids.values()}
    player_records = gen_players(teams_by_id)
    for p in player_records:
        cur.execute(
            """INSERT INTO players (full_name, country, playing_role, batting_style, bowling_style, date_of_birth)
               VALUES (?,?,?,?,?,?)""",
            (p["full_name"], p["country"], p["playing_role"], p["batting_style"], p["bowling_style"], p["date_of_birth"]),
        )
        pid = cur.lastrowid
        players_by_team[p["team_id"]].append(pid)

    # --- Series (mix of years, several starting in 2024 per spec) ---
    series_ids = []
    series_pool = []
    for yr in range(2019, 2027):
        n = 3 if yr != 2024 else 5
        for _ in range(n):
            mtype = random.choices(FORMATS, weights=FORMAT_WEIGHTS, k=1)[0]
            host = random.choice(TEAMS)[1]
            start = date(yr, random.randint(1, 12), random.randint(1, 28))
            if start > TODAY:
                continue
            total_matches = random.choice([2, 3, 5]) if mtype != "Test" else random.choice([2, 3])
            name = f"{host} {mtype} Series {yr}"
            series_pool.append((name, host, mtype, start.isoformat(), total_matches))
    for s in series_pool:
        cur.execute(
            "INSERT INTO series (series_name, host_country, match_type, start_date, total_matches) VALUES (?,?,?,?,?)",
            s,
        )
        series_ids.append((cur.lastrowid, s[2], s[3]))  # (id, match_type, start_date)

    # --- Matches ---
    team_id_list = list(team_ids.values())
    match_rows = []
    N_MATCHES = 260
    recent_slots = 25  # force a healthy number into the last 30-60 days for Q2/Q10

    for i in range(N_MATCHES):
        series_id, s_mtype, s_start = random.choice(series_ids)
        if i < recent_slots:
            m_date = TODAY - timedelta(days=random.randint(0, 28))
        else:
            m_date = random_date_weighted()
        match_type = s_mtype
        t1, t2 = random.sample(team_id_list, 2)
        venue_id = random.choice(venue_ids)
        toss_winner = random.choice([t1, t2])
        toss_decision = random.choice(["bat", "bowl"])
        status = "completed" if m_date <= TODAY else "upcoming"
        # small number of true "live" matches today for the demo page
        if 0 <= (TODAY - m_date).days <= 0 and i < 3:
            status = "live"

        team1_name = teams_by_id[t1][0]
        team2_name = teams_by_id[t2][0]
        desc = f"{team1_name} vs {team2_name}, {match_type}"

        winner = None
        margin = None
        vtype = None
        if status == "completed":
            winner = random.choice([t1, t2, None])
            if winner is None:
                winner = random.choice([t1, t2])  # ties are rare edge cases; keep it simple
            vtype = random.choice(["runs", "wickets"])
            margin = random.randint(5, 250) if vtype == "runs" else random.randint(1, 10)

        match_rows.append({
            "series_id": series_id, "team1_id": t1, "team2_id": t2, "venue_id": venue_id,
            "match_date": m_date.isoformat(), "match_type": match_type, "match_description": desc,
            "winner_team_id": winner, "victory_margin": margin, "victory_type": vtype,
            "toss_winner_id": toss_winner, "toss_decision": toss_decision, "match_status": status,
        })

    for m in match_rows:
        cur.execute(
            """INSERT INTO matches
               (series_id, team1_id, team2_id, venue_id, match_date, match_type, match_description,
                winner_team_id, victory_margin, victory_type, toss_winner_id, toss_decision, match_status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (m["series_id"], m["team1_id"], m["team2_id"], m["venue_id"], m["match_date"], m["match_type"],
             m["match_description"], m["winner_team_id"], m["victory_margin"], m["victory_type"],
             m["toss_winner_id"], m["toss_decision"], m["match_status"]),
        )
        m["match_id"] = cur.lastrowid
        if m["match_status"] in ("completed", "live"):
            roster1 = players_by_team[m["team1_id"]]
            roster2 = players_by_team[m["team2_id"]]
            if len(roster1) >= 6 and len(roster2) >= 6:
                build_scorecards(m, roster1, roster2, cur)

    conn.commit()
    conn.close()

    print(f"Seeded: {len(team_ids)} teams, {len(player_records)} players, "
          f"{len(venue_ids)} venues, {len(series_ids)} series, {len(match_rows)} matches.")
    print(f"Database ready at: {config.SQLITE_PATH if config.DB_ENGINE == 'sqlite' else config.DB_ENGINE}")


if __name__ == "__main__":
    main()
