-- Migration 004: idempotent award predictions + ranked-list metadata
ALTER TABLE award_predictions
    ADD COLUMN IF NOT EXISTS team_id INT,
    ADD COLUMN IF NOT EXISTS stats_snapshot JSONB;
ALTER TABLE award_predictions ALTER COLUMN award_share_pct TYPE NUMERIC(6,4);
CREATE UNIQUE INDEX IF NOT EXISTS award_predictions_uq ON award_predictions(season_label, award, player_id);
