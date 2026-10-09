-- Migration 003: roster / contract metadata sourced from ESPN
ALTER TABLE players
    ADD COLUMN IF NOT EXISTS espn_id       BIGINT,
    ADD COLUMN IF NOT EXISTS height_in     INT,
    ADD COLUMN IF NOT EXISTS weight_lb     INT,
    ADD COLUMN IF NOT EXISTS headshot_url  TEXT,
    ADD COLUMN IF NOT EXISTS experience    INT,
    ADD COLUMN IF NOT EXISTS college       TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS players_espn_id_uq ON players(espn_id) WHERE espn_id IS NOT NULL;

ALTER TABLE contracts
    ADD COLUMN IF NOT EXISTS option_type   INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS trade_restriction BOOLEAN DEFAULT FALSE;
CREATE UNIQUE INDEX IF NOT EXISTS contracts_player_season_uq ON contracts(player_id, season_label);

ALTER TABLE injuries ADD COLUMN IF NOT EXISTS espn_status TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS injuries_player_uq ON injuries(player_id);

-- model output tables need one row per game / award slot so syncs can be idempotent
CREATE UNIQUE INDEX IF NOT EXISTS game_predictions_game_model_uq ON game_predictions(game_id, model_type);
