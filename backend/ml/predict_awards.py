"""
Score the current award races from our own game logs and upsert into award_predictions.

    python ml/predict_awards.py [--season 2026]     # season = BR convention, 2026 means 2025-26

Default season: the newest one where at least one team has played >= 10 games.
"""
import argparse
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.dirname(__file__))
from award_features import AWARDS, FEATS, award_pool, build_features  # noqa: E402
from features import connect  # noqa: E402

MODEL_DIR = os.path.dirname(__file__)
REGULAR = "('Regular Season','NBA Emirates Cup')"   # the Cup final ('Emirates NBA Cup') does not count toward records
SEASON = "(EXTRACT(YEAR FROM (game_date - INTERVAL '6 months'))::int + 1)"


def load(conn):
    logs = pd.read_sql(f"""
        SELECT {SEASON} AS season, player_id,
               COUNT(*) g, SUM(is_started::int) gs, SUM(min_played) mp,
               SUM(pts) pts, SUM(reb) trb, SUM(ast) ast, SUM(stl) stl, SUM(blk) blk, SUM(tov) tov,
               SUM(dreb) drb, SUM(fga) fga, SUM(fta) fta, SUM(fgm) fg, SUM(fg3m) x3, SUM(ftm) ft,
               (ARRAY_AGG(team_id ORDER BY game_date DESC))[1] AS team_id
        FROM player_game_logs WHERE COALESCE(game_type,'Regular Season') IN {REGULAR}
        GROUP BY 1, 2""", conn)
    first = pd.read_sql("SELECT player_id, MIN(" + SEASON + ") AS first_season FROM player_game_logs GROUP BY 1", conn)
    team = pd.read_sql(f"""
        SELECT {SEASON} AS season, team_id AS team_key, COUNT(*) team_games,
               AVG(win::int) team_win_pct, AVG(pts - opp_pts) team_mov, AVG(def_rating) team_drtg
        FROM team_game_stats WHERE COALESCE(game_type,'Regular Season') IN {REGULAR}
        GROUP BY 1, 2""", conn)
    names = pd.read_sql("SELECT player_id, full_name AS name FROM players", conn)
    return logs, first, team, names


def main(season):
    conn = connect()
    logs, first, team, names = load(conn)
    if season is None:
        by = team.groupby('season')['team_games'].max()
        season = int(by[by >= 10].index.max())
    label = f"{season - 1}-{str(season)[2:]}"
    games_by_season = team.groupby('season')['team_games'].max()
    d = logs.merge(first, on='player_id').merge(names, on='player_id', how='left')
    d['player_key'] = d['player_id']
    d['team_key'] = d['team_id']
    d['team_games'] = d['season'].map(games_by_season)
    d['mp'] = d['mp'].astype(float)
    for c in ['g', 'gs', 'pts', 'trb', 'ast', 'stl', 'blk', 'tov', 'drb', 'fga', 'fta', 'fg', 'x3', 'ft']:
        d[c] = d[c].astype(float)
    team = team.drop(columns='team_games')
    feat, _ = build_features(d.drop(columns=['team_id']), team)
    cur_df = feat[feat['season'] == season]
    team_ids = d.set_index(['season', 'player_id'])['team_id']

    rows = []
    for key in AWARDS:
        model = joblib.load(os.path.join(MODEL_DIR, f'awards_{key}.pkl'))
        pool = award_pool(cur_df, key)
        if pool.empty:
            continue
        pred = np.clip(model.predict(pool[FEATS]), 0, 1)
        ranked = pool.assign(pred=pred).sort_values('pred', ascending=False).head(15)
        print(f"\n{key.upper()} {label}")
        for rank, r in enumerate(ranked.itertuples(), 1):
            snap = {k: (None if pd.isna(getattr(r, k)) else round(float(getattr(r, k)), 2))
                    for k in ['pts', 'trb', 'ast', 'stl', 'blk', 'ts', 'g', 'team_win_pct']}
            tid = int(team_ids.loc[(season, r.player_id)])
            rows.append((label, key.upper(), int(r.player_id), rank, round(float(r.pred), 4), tid, json.dumps(snap)))
            if rank <= 5:
                print(f"  {rank}. {r.name:26s} {r.pred:.3f}  {snap['pts']}/{snap['trb']}/{snap['ast']}  g={int(snap['g'])}")
    cur = conn.cursor()
    cur.execute("DELETE FROM award_predictions WHERE season_label = %s", (label,))
    execute_values(cur, """INSERT INTO award_predictions (season_label, award, player_id, predicted_rank, award_share_pct,
                             team_id, stats_snapshot, predicted_at) VALUES %s""",
                   rows, template="(%s,%s,%s,%s,%s,%s,%s, now())")
    conn.commit()
    print(f"\nwrote {len(rows)} rows for {label}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--season', type=int)
    main(ap.parse_args().season)
