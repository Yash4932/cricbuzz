-- =============================================================================
-- Cricbuzz LiveStats -- Database Schema
-- Normalized to 3NF: no repeating groups, every non-key column depends only
-- on the primary key (no partial or transitive dependencies).
-- Written in SQLite dialect; portable to Postgres/MySQL with minor tweaks
-- (SERIAL/AUTO_INCREMENT instead of AUTOINCREMENT, etc.)
-- =============================================================================

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS fielding_scorecards;
DROP TABLE IF EXISTS bowling_scorecards;
DROP TABLE IF EXISTS batting_scorecards;
DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS series;
DROP TABLE IF EXISTS venues;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS teams;

-- -----------------------------------------------------------------------------
-- TEAMS
-- -----------------------------------------------------------------------------
CREATE TABLE teams (
    team_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name   TEXT NOT NULL UNIQUE,
    country     TEXT NOT NULL
);

-- -----------------------------------------------------------------------------
-- PLAYERS
-- -----------------------------------------------------------------------------
CREATE TABLE players (
    player_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name      TEXT NOT NULL,
    country        TEXT NOT NULL,
    playing_role   TEXT NOT NULL CHECK (playing_role IN
                       ('Batsman','Bowler','All-rounder','Wicket-keeper')),
    batting_style  TEXT,
    bowling_style  TEXT,
    date_of_birth  DATE
);

CREATE INDEX idx_players_country ON players(country);
CREATE INDEX idx_players_role    ON players(playing_role);

-- -----------------------------------------------------------------------------
-- VENUES
-- -----------------------------------------------------------------------------
CREATE TABLE venues (
    venue_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_name   TEXT NOT NULL,
    city         TEXT NOT NULL,
    country      TEXT NOT NULL,
    capacity     INTEGER NOT NULL CHECK (capacity >= 0)
);

-- -----------------------------------------------------------------------------
-- SERIES
-- -----------------------------------------------------------------------------
CREATE TABLE series (
    series_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    series_name     TEXT NOT NULL,
    host_country    TEXT NOT NULL,
    match_type      TEXT NOT NULL CHECK (match_type IN ('Test','ODI','T20I')),
    start_date      DATE NOT NULL,
    total_matches   INTEGER NOT NULL CHECK (total_matches > 0)
);

-- -----------------------------------------------------------------------------
-- MATCHES
-- -----------------------------------------------------------------------------
CREATE TABLE matches (
    match_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id           INTEGER NOT NULL REFERENCES series(series_id),
    team1_id             INTEGER NOT NULL REFERENCES teams(team_id),
    team2_id             INTEGER NOT NULL REFERENCES teams(team_id),
    venue_id            INTEGER NOT NULL REFERENCES venues(venue_id),
    match_date          DATE NOT NULL,
    match_type          TEXT NOT NULL CHECK (match_type IN ('Test','ODI','T20I')),
    match_description   TEXT NOT NULL,
    winner_team_id       INTEGER REFERENCES teams(team_id),
    victory_margin       INTEGER,
    victory_type         TEXT CHECK (victory_type IN ('runs','wickets', NULL)),
    toss_winner_id       INTEGER REFERENCES teams(team_id),
    toss_decision        TEXT CHECK (toss_decision IN ('bat','bowl', NULL)),
    match_status         TEXT NOT NULL DEFAULT 'completed'
                          CHECK (match_status IN ('completed','live','upcoming')),
    CHECK (team1_id <> team2_id)
);

CREATE INDEX idx_matches_date       ON matches(match_date);
CREATE INDEX idx_matches_type       ON matches(match_type);
CREATE INDEX idx_matches_series     ON matches(series_id);
CREATE INDEX idx_matches_venue      ON matches(venue_id);
CREATE INDEX idx_matches_winner     ON matches(winner_team_id);
CREATE INDEX idx_matches_status     ON matches(match_status);

-- -----------------------------------------------------------------------------
-- BATTING SCORECARDS  (one row per player, per innings, per match)
-- -----------------------------------------------------------------------------
CREATE TABLE batting_scorecards (
    scorecard_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id         INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    innings_number   INTEGER NOT NULL CHECK (innings_number IN (1,2,3,4)),
    player_id        INTEGER NOT NULL REFERENCES players(player_id),
    team_id          INTEGER NOT NULL REFERENCES teams(team_id),
    batting_position INTEGER NOT NULL CHECK (batting_position BETWEEN 1 AND 11),
    runs_scored      INTEGER NOT NULL DEFAULT 0 CHECK (runs_scored >= 0),
    balls_faced      INTEGER NOT NULL DEFAULT 0 CHECK (balls_faced >= 0),
    fours            INTEGER NOT NULL DEFAULT 0,
    sixes            INTEGER NOT NULL DEFAULT 0,
    dismissal_type   TEXT,
    UNIQUE (match_id, innings_number, player_id)
);

CREATE INDEX idx_batting_player   ON batting_scorecards(player_id);
CREATE INDEX idx_batting_match    ON batting_scorecards(match_id);
CREATE INDEX idx_batting_position ON batting_scorecards(batting_position);

-- -----------------------------------------------------------------------------
-- BOWLING SCORECARDS
-- -----------------------------------------------------------------------------
CREATE TABLE bowling_scorecards (
    scorecard_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    innings_number  INTEGER NOT NULL CHECK (innings_number IN (1,2,3,4)),
    player_id       INTEGER NOT NULL REFERENCES players(player_id),
    team_id         INTEGER NOT NULL REFERENCES teams(team_id),
    overs_bowled    REAL NOT NULL DEFAULT 0 CHECK (overs_bowled >= 0),
    runs_conceded   INTEGER NOT NULL DEFAULT 0 CHECK (runs_conceded >= 0),
    wickets_taken   INTEGER NOT NULL DEFAULT 0 CHECK (wickets_taken >= 0),
    UNIQUE (match_id, innings_number, player_id)
);

CREATE INDEX idx_bowling_player ON bowling_scorecards(player_id);
CREATE INDEX idx_bowling_match  ON bowling_scorecards(match_id);

-- -----------------------------------------------------------------------------
-- FIELDING SCORECARDS
-- -----------------------------------------------------------------------------
CREATE TABLE fielding_scorecards (
    scorecard_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id       INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    player_id      INTEGER NOT NULL REFERENCES players(player_id),
    team_id        INTEGER NOT NULL REFERENCES teams(team_id),
    catches        INTEGER NOT NULL DEFAULT 0,
    stumpings      INTEGER NOT NULL DEFAULT 0,
    UNIQUE (match_id, player_id)
);

CREATE INDEX idx_fielding_player ON fielding_scorecards(player_id);
