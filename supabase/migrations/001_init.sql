-- TEAMS
CREATE TABLE teams (
    team_id         INT PRIMARY KEY,           -- from nba_api
    full_name       VARCHAR(100),
    abbreviation    VARCHAR(5),
    city            VARCHAR(50),
    conference      VARCHAR(4),                -- 'East' | 'West'
    division        VARCHAR(20),
    is_active       BOOLEAN DEFAULT TRUE
);

-- PLAYERS
CREATE TABLE players (
    player_id       INT PRIMARY KEY,
    full_name       VARCHAR(150),
    team_id         INT REFERENCES teams(team_id),
    position        VARCHAR(10),               -- PG, SG, SF, PF, C
    age             INT,
    jersey_number   VARCHAR(5),
    is_active       BOOLEAN DEFAULT TRUE,
    is_custom       BOOLEAN DEFAULT FALSE      -- for custom team maker
);

-- SEASONS
CREATE TABLE seasons (
    season_id       SERIAL PRIMARY KEY,
    season_label    VARCHAR(10),               -- '2024-25'
    start_date      DATE,
    end_date        DATE
);

-- GAMES (schedule + results)
CREATE TABLE games (
    game_id         VARCHAR(20) PRIMARY KEY,   -- nba_api game_id
    season_id       INT REFERENCES seasons(season_id),
    game_date       DATE,
    home_team_id    INT REFERENCES teams(team_id),
    away_team_id    INT REFERENCES teams(team_id),
    home_score      INT,
    away_score      INT,
    status          VARCHAR(20),               -- 'Scheduled' | 'Live' | 'Final'
    home_days_rest  INT,                       -- CRITICAL: back-to-back flag
    away_days_rest  INT,
    quarter         INT,                       -- current quarter if Live
    time_remaining  VARCHAR(10)
);

-- TEAM GAME STATS (one row per team per game)
CREATE TABLE team_game_stats (
    id              SERIAL PRIMARY KEY,
    game_id         VARCHAR(20) REFERENCES games(game_id),
    team_id         INT REFERENCES teams(team_id),
    is_home         BOOLEAN,
    -- Raw counting stats
    pts             INT,
    reb             INT,
    ast             INT,
    stl             INT,
    blk             INT,
    tov             INT,
    -- Shooting
    fgm             INT,
    fga             INT,
    fg3m            INT,
    fg3a            INT,
    ftm             INT,
    fta             INT,
    -- Advanced (computed or pulled from nba_api)
    efg_pct         NUMERIC(5,4),              -- (FGM + 0.5*3PM) / FGA
    tov_pct         NUMERIC(5,4),              -- TOV / (FGA + 0.44*FTA + TOV)
    oreb_pct        NUMERIC(5,4),
    ft_rate         NUMERIC(5,4),              -- FTA / FGA
    off_rating      NUMERIC(6,2),
    def_rating      NUMERIC(6,2),
    net_rating      NUMERIC(6,2),
    pace            NUMERIC(6,2),
    -- Quarter breakdown (for live prediction)
    q1_pts          INT,
    q2_pts          INT,
    q3_pts          INT,
    q4_pts          INT
);

-- PLAYER GAME LOGS (one row per player per game)
CREATE TABLE player_game_logs (
    id              SERIAL PRIMARY KEY,
    game_id         VARCHAR(20) REFERENCES games(game_id),
    player_id       INT REFERENCES players(player_id),
    team_id         INT REFERENCES teams(team_id),
    min             NUMERIC(5,2),
    pts             INT,
    reb             INT,
    ast             INT,
    stl             INT,
    blk             INT,
    tov             INT,
    fgm             INT,
    fga             INT,
    fg3m            INT,
    fg3a            INT,
    ftm             INT,
    fta             INT,
    usg_pct         NUMERIC(5,4),
    per             NUMERIC(6,2),              -- Player Efficiency Rating
    ws_48           NUMERIC(6,4),              -- Win Shares per 48
    bpm             NUMERIC(6,2),              -- Box Plus/Minus
    epm             NUMERIC(6,2),              -- Estimated Plus-Minus
    ts_pct          NUMERIC(5,4),
    ast_pct         NUMERIC(5,4),
    is_started      BOOLEAN
);

-- ROLLING TEAM STATS (updated nightly by cron)
CREATE TABLE team_rolling_stats (
    id              SERIAL PRIMARY KEY,
    team_id         INT REFERENCES teams(team_id),
    as_of_date      DATE,
    stat_window     INT,                       -- 5 or 10 games
    efg_pct_roll    NUMERIC(5,4),
    tov_pct_roll    NUMERIC(5,4),
    oreb_pct_roll   NUMERIC(5,4),
    ft_rate_roll    NUMERIC(5,4),
    net_rating_roll NUMERIC(6,2),
    off_rating_roll NUMERIC(6,2),
    def_rating_roll NUMERIC(6,2),
    pace_roll       NUMERIC(6,2),
    fga_avg_roll    NUMERIC(6,2)
);

-- PLAYER ROLLING STATS (updated nightly)
CREATE TABLE player_rolling_stats (
    id              SERIAL PRIMARY KEY,
    player_id       INT REFERENCES players(player_id),
    as_of_date      DATE,
    stat_window     INT,
    pts_avg         NUMERIC(5,2),
    reb_avg         NUMERIC(5,2),
    ast_avg         NUMERIC(5,2),
    fg_pct_roll     NUMERIC(5,4),
    usg_pct_roll    NUMERIC(5,4),
    ts_pct_roll     NUMERIC(5,4),
    epm_rank        INT                        -- current season EPM rank
);

-- POSITIONAL DEFENSIVE RATINGS (per team, per position)
CREATE TABLE team_positional_defense (
    id              SERIAL PRIMARY KEY,
    team_id         INT REFERENCES teams(team_id),
    position        VARCHAR(10),
    games_sample    INT,                       -- last N games
    pts_allowed_avg NUMERIC(5,2),
    fg_pct_allowed  NUMERIC(5,4),
    reb_allowed_avg NUMERIC(5,2),
    def_rating_vs   NUMERIC(6,2),
    as_of_date      DATE
);

-- TEAM DEFENSIVE CLUSTERS (K-Means output)
CREATE TABLE team_defensive_clusters (
    team_id         INT REFERENCES teams(team_id),
    season_label    VARCHAR(10),
    cluster_id      INT,                       -- 0-4: 5 archetypes
    cluster_label   VARCHAR(50),               -- 'Heavy Rim Protection' etc.
    PRIMARY KEY (team_id, season_label)
);

-- PLAYER SEASON RANKINGS (nightly snapshot)
CREATE TABLE player_season_rankings (
    id              SERIAL PRIMARY KEY,
    player_id       INT REFERENCES players(player_id),
    season_label    VARCHAR(10),
    as_of_date      DATE,
    epm_rank        INT,
    per_rank        INT,
    ws_rank         INT,
    is_top_10       BOOLEAN,
    is_top_25       BOOLEAN,
    is_top_50       BOOLEAN
);

-- CONTRACTS
CREATE TABLE contracts (
    id              SERIAL PRIMARY KEY,
    player_id       INT REFERENCES players(player_id),
    team_id         INT REFERENCES teams(team_id),
    season_label    VARCHAR(10),
    salary          BIGINT,                    -- in dollars
    years_remaining INT,
    is_rookie_deal  BOOLEAN DEFAULT FALSE,
    is_max          BOOLEAN DEFAULT FALSE,
    is_expiring     BOOLEAN DEFAULT FALSE,
    trade_kpi       NUMERIC(5,2)               -- Trade Value Score 0-100
);

-- SALARY CAP SETTINGS
CREATE TABLE salary_cap_settings (
    season_label    VARCHAR(10) PRIMARY KEY,
    salary_cap      BIGINT,
    luxury_tax      BIGINT,
    apron_1         BIGINT,
    apron_2         BIGINT
);

-- GAME PREDICTIONS
CREATE TABLE game_predictions (
    id              SERIAL PRIMARY KEY,
    game_id         VARCHAR(20) REFERENCES games(game_id),
    model_type      VARCHAR(20),               -- 'static' | 'live'
    predicted_at    TIMESTAMP,
    home_win_prob   NUMERIC(5,4),
    away_win_prob   NUMERIC(5,4),
    key_driver      TEXT,                      -- human readable XGBoost explainer
    feature_snapshot JSONB                     -- full feature vector at time of prediction
);

-- PLAYER PROP PREDICTIONS
CREATE TABLE player_prop_predictions (
    id              SERIAL PRIMARY KEY,
    game_id         VARCHAR(20) REFERENCES games(game_id),
    player_id       INT REFERENCES players(player_id),
    prop_type       VARCHAR(30),               -- 'pts', 'reb', 'ast', 'pts+reb+ast'
    line            NUMERIC(5,2),              -- sportsbook line
    over_prob       NUMERIC(5,4),
    under_prob      NUMERIC(5,4),
    model_type      VARCHAR(20),
    predicted_at    TIMESTAMP,
    key_driver      TEXT
);

-- BETTING ODDS (from The Odds API)
CREATE TABLE betting_odds (
    id              SERIAL PRIMARY KEY,
    game_id         VARCHAR(20),
    player_id       INT,                       -- NULL for game lines
    bookmaker       VARCHAR(50),
    market          VARCHAR(50),               -- 'spreads', 'totals', 'player_pts'
    outcome_name    VARCHAR(100),
    price           NUMERIC(8,2),              -- American odds
    line            NUMERIC(6,2),              -- over/under line
    fetched_at      TIMESTAMP
);

-- INJURIES
CREATE TABLE injuries (
    id              SERIAL PRIMARY KEY,
    player_id       INT REFERENCES players(player_id),
    status          VARCHAR(20),               -- 'Out', 'Questionable', 'Doubtful', 'GTD'
    reason          TEXT,
    updated_at      TIMESTAMP
);

-- AWARD PREDICTIONS
CREATE TABLE award_predictions (
    id              SERIAL PRIMARY KEY,
    season_label    VARCHAR(10),
    award           VARCHAR(20),               -- 'MVP', 'ROY', 'DPOY', 'SMOY', '6MOY'
    player_id       INT REFERENCES players(player_id),
    predicted_rank  INT,
    award_share_pct NUMERIC(5,4),
    predicted_at    TIMESTAMP
);

-- DRAFT PICKS
CREATE TABLE draft_picks (
    id              SERIAL PRIMARY KEY,
    owning_team_id  INT REFERENCES teams(team_id),
    original_team_id INT REFERENCES teams(team_id),
    year            INT,
    round           INT,                       -- 1 or 2
    pick_type       VARCHAR(20),               -- 'lottery', 'mid', 'late'
    protection      VARCHAR(100),
    trade_value     NUMERIC(5,2)
);

-- TRADE SIMULATIONS
CREATE TABLE trade_simulations (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMP,
    is_custom       BOOLEAN DEFAULT FALSE,
    status          VARCHAR(20),               -- 'proposed', 'validated', 'simulated'
    validation_error TEXT
);

-- TRADE LEGS (which assets move in each direction)
CREATE TABLE trade_legs (
    id              SERIAL PRIMARY KEY,
    trade_id        INT REFERENCES trade_simulations(id),
    from_team_id    INT REFERENCES teams(team_id),
    to_team_id      INT REFERENCES teams(team_id),
    asset_type      VARCHAR(10),               -- 'player' | 'pick'
    player_id       INT,
    pick_id         INT
);

-- POST-TRADE PROJECTIONS
CREATE TABLE trade_projections (
    id              SERIAL PRIMARY KEY,
    trade_id        INT REFERENCES trade_simulations(id),
    team_id         INT REFERENCES teams(team_id),
    proj_wins       NUMERIC(5,2),
    proj_losses     NUMERIC(5,2),
    proj_efg        NUMERIC(5,4),
    proj_net_rating NUMERIC(6,2),
    delta_wins      NUMERIC(5,2),              -- change vs current projection
    player_impact   JSONB                      -- per-player usage/stat change
);

-- CUSTOM TEAMS
CREATE TABLE custom_teams (
    id              SERIAL PRIMARY KEY,
    created_at      TIMESTAMP,
    team_name       VARCHAR(100),
    roster          JSONB,                     -- [{player_id, usg_override}]
    is_random       BOOLEAN DEFAULT FALSE
);

-- CUSTOM TEAM PREDICTIONS
CREATE TABLE custom_team_predictions (
    id              SERIAL PRIMARY KEY,
    custom_team_id  INT REFERENCES custom_teams(id),
    vs_team_id      INT REFERENCES teams(team_id),
    win_prob        NUMERIC(5,4),
    proj_pts        NUMERIC(5,2),
    proj_allowed    NUMERIC(5,2),
    key_driver      TEXT
);

-- MATCHUP PREDICTOR VIEW
CREATE OR REPLACE VIEW matchup_predictor_input AS
SELECT
    g.game_id,
    g.game_date,
    g.home_team_id,
    g.away_team_id,
    g.home_days_rest,
    g.away_days_rest,
    (g.home_days_rest = 1)::INT AS is_b2b_home,
    (g.away_days_rest = 1)::INT AS is_b2b_away,
    h.efg_pct_roll   - a.efg_pct_roll   AS efg_pct_diff,
    h.tov_pct_roll   - a.tov_pct_roll   AS tov_pct_diff,
    h.oreb_pct_roll  - a.oreb_pct_roll  AS oreb_pct_diff,
    h.ft_rate_roll   - a.ft_rate_roll   AS ft_rate_diff,
    h.net_rating_roll- a.net_rating_roll AS net_rating_diff,
    h.fga_avg_roll   - a.fga_avg_roll   AS fga_diff,
    hr.is_top_10::INT AS has_top10_home,
    ar.is_top_10::INT AS has_top10_away,
    hr.is_top_25::INT AS has_top25_home,
    ar.is_top_25::INT AS has_top25_away
FROM games g
JOIN team_rolling_stats h ON h.team_id = g.home_team_id AND h.stat_window = 10
JOIN team_rolling_stats a ON a.team_id = g.away_team_id AND a.stat_window = 10
LEFT JOIN LATERAL (
    SELECT COALESCE(MAX(r.is_top_10::INT), 0) as is_top_10, COALESCE(MAX(r.is_top_25::INT), 0) as is_top_25
    FROM player_season_rankings r
    JOIN players p ON r.player_id = p.player_id
    WHERE p.team_id = g.home_team_id
) hr ON true
LEFT JOIN LATERAL (
    SELECT COALESCE(MAX(r.is_top_10::INT), 0) as is_top_10, COALESCE(MAX(r.is_top_25::INT), 0) as is_top_25
    FROM player_season_rankings r
    JOIN players p ON r.player_id = p.player_id
    WHERE p.team_id = g.away_team_id
) ar ON true
WHERE g.status IN ('Scheduled', 'Live');
