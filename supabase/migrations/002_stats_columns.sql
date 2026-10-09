-- Migration 002: Add missing columns to team_game_stats and player_game_logs
-- Run this in the Supabase SQL Editor

-- team_game_stats additions
ALTER TABLE team_game_stats
    ADD COLUMN IF NOT EXISTS opp_team_id     INT REFERENCES teams(team_id),
    ADD COLUMN IF NOT EXISTS win             BOOLEAN,
    ADD COLUMN IF NOT EXISTS opp_pts         INT,
    ADD COLUMN IF NOT EXISTS fg_pct          NUMERIC(5,4),
    ADD COLUMN IF NOT EXISTS fg3_pct         NUMERIC(5,4),
    ADD COLUMN IF NOT EXISTS ft_pct          NUMERIC(5,4),
    ADD COLUMN IF NOT EXISTS oreb            INT,
    ADD COLUMN IF NOT EXISTS dreb            INT,
    ADD COLUMN IF NOT EXISTS pf              INT,
    ADD COLUMN IF NOT EXISTS pts_paint       INT,
    ADD COLUMN IF NOT EXISTS pts_fb          INT,
    ADD COLUMN IF NOT EXISTS bench_pts       INT,
    ADD COLUMN IF NOT EXISTS plus_minus      NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS season_wins     INT,
    ADD COLUMN IF NOT EXISTS season_losses   INT,
    ADD COLUMN IF NOT EXISTS game_date       DATE,
    ADD COLUMN IF NOT EXISTS game_type       VARCHAR(20);

-- Unique constraint so upsert works (Postgres has no "ADD CONSTRAINT IF NOT EXISTS")
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'team_game_stats_game_team_uq') THEN
        ALTER TABLE team_game_stats ADD CONSTRAINT team_game_stats_game_team_uq UNIQUE (game_id, team_id);
    END IF;
END $$;

-- player_game_logs additions
ALTER TABLE player_game_logs
    ADD COLUMN IF NOT EXISTS opp_team_id     INT REFERENCES teams(team_id),
    ADD COLUMN IF NOT EXISTS win             BOOLEAN,
    ADD COLUMN IF NOT EXISTS fg_pct          NUMERIC(5,4),
    ADD COLUMN IF NOT EXISTS fg3_pct         NUMERIC(5,4),
    ADD COLUMN IF NOT EXISTS ft_pct          NUMERIC(5,4),
    ADD COLUMN IF NOT EXISTS oreb            INT,
    ADD COLUMN IF NOT EXISTS dreb            INT,
    ADD COLUMN IF NOT EXISTS pf              INT,
    ADD COLUMN IF NOT EXISTS plus_minus      NUMERIC(6,2),
    ADD COLUMN IF NOT EXISTS is_started      BOOLEAN,
    ADD COLUMN IF NOT EXISTS game_date       DATE,
    ADD COLUMN IF NOT EXISTS game_type       VARCHAR(20);

-- Rename min column to be safe (original schema uses min which conflicts with SQL keyword on some dialects)
-- Only run if you have no data yet in the column
ALTER TABLE player_game_logs
    ADD COLUMN IF NOT EXISTS min_played      NUMERIC(5,2);

-- Unique constraint so upsert works (Postgres has no "ADD CONSTRAINT IF NOT EXISTS")
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'player_game_logs_game_player_uq') THEN
        ALTER TABLE player_game_logs ADD CONSTRAINT player_game_logs_game_player_uq UNIQUE (game_id, player_id);
    END IF;
END $$;

-- Also add a view for quick season averages per player.
-- Anchored to the latest loaded game_date (not CURRENT_DATE) since this is a finite historical
-- dataset, not a live feed -- a wall-clock-relative window would go empty during any offseason.
CREATE OR REPLACE VIEW player_season_avgs AS
SELECT
    p.player_id,
    p.full_name,
    p.team_id,
    ROUND(AVG(gl.pts)::numeric, 1)   AS pts_avg,
    ROUND(AVG(gl.reb)::numeric, 1)   AS reb_avg,
    ROUND(AVG(gl.ast)::numeric, 1)   AS ast_avg,
    ROUND(AVG(gl.stl)::numeric, 1)   AS stl_avg,
    ROUND(AVG(gl.blk)::numeric, 1)   AS blk_avg,
    ROUND(AVG(gl.fg_pct)::numeric, 3) AS fg_pct_avg,
    ROUND(AVG(gl.fg3_pct)::numeric, 3) AS fg3_pct_avg,
    ROUND(AVG(gl.plus_minus)::numeric, 1) AS pm_avg,
    COUNT(*)                          AS games_played
FROM player_game_logs gl
JOIN players p ON p.player_id = gl.player_id
WHERE gl.game_date >= (SELECT MAX(game_date) FROM player_game_logs) - INTERVAL '90 days'
GROUP BY p.player_id, p.full_name, p.team_id;

-- Season averages per team (same anchoring rationale as player_season_avgs above)
CREATE OR REPLACE VIEW team_season_avgs AS
SELECT
    t.team_id,
    t.abbreviation,
    t.full_name,
    ROUND(AVG(tgs.pts)::numeric, 1)      AS pts_avg,
    ROUND(AVG(tgs.reb)::numeric, 1)      AS reb_avg,
    ROUND(AVG(tgs.ast)::numeric, 1)      AS ast_avg,
    ROUND(AVG(tgs.efg_pct)::numeric, 3)  AS efg_pct_avg,
    ROUND(AVG(tgs.tov_pct)::numeric, 3)  AS tov_pct_avg,
    ROUND(AVG(tgs.ft_rate)::numeric, 3)  AS ft_rate_avg,
    SUM(CASE WHEN tgs.win THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN NOT tgs.win THEN 1 ELSE 0 END) AS losses,
    COUNT(*) AS games_played
FROM team_game_stats tgs
JOIN teams t ON t.team_id = tgs.team_id
WHERE tgs.game_date >= (SELECT MAX(game_date) FROM team_game_stats) - INTERVAL '180 days'
GROUP BY t.team_id, t.abbreviation, t.full_name;
