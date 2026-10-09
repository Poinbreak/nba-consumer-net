-- Migration 006: indexes for the player/team/scoreboard pages
CREATE INDEX IF NOT EXISTS idx_pgl_player_date ON player_game_logs (player_id, game_date DESC);
CREATE INDEX IF NOT EXISTS idx_pgl_team_date   ON player_game_logs (team_id, game_date);
CREATE INDEX IF NOT EXISTS idx_pgl_date        ON player_game_logs (game_date);
CREATE INDEX IF NOT EXISTS idx_tgs_team_date   ON team_game_stats (team_id, game_date);
CREATE INDEX IF NOT EXISTS idx_games_date      ON games (game_date);
CREATE INDEX IF NOT EXISTS idx_games_home      ON games (home_team_id, game_date);
CREATE INDEX IF NOT EXISTS idx_games_away      ON games (away_team_id, game_date);
CREATE INDEX IF NOT EXISTS idx_players_team    ON players (team_id) WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_players_name    ON players (lower(full_name));
