"""
Predict every scheduled game in the DB and upsert into game_predictions.

    python ml/predict_upcoming.py [--days 14]
"""
import argparse
import json
import os
import sys
from datetime import date, timedelta

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.dirname(__file__))
from features import connect, load_team_games, predict_features  # noqa: E402

MODEL_DIR = os.path.dirname(__file__)
NAMES = {
    'elo': 'Elo rating', 'home_rest': 'Home rest', 'away_rest': 'Away rest',
    'home_b2b': 'Home back-to-back', 'away_b2b': 'Away back-to-back', 'is_playoffs': 'Playoff game',
    'season_win_pct': 'season record', 'net_rating': 'net rating', 'off_rating': 'offense',
    'def_rating': 'defense', 'efg_pct': 'shooting efficiency', 'tov_pct': 'turnover rate',
    'oreb_pct': 'offensive rebounding', 'ft_rate': 'free-throw rate', 'pace': 'pace', 'fga': 'shot volume',
    'rest_days': 'rest', 'games_last7': 'schedule load',
}


def describe(feature, value, shap_val):
    base = feature.replace('_diff', '')
    window = ''
    if '_r' in base and base.rsplit('_r', 1)[1].isdigit():
        base, w = base.rsplit('_r', 1)
        window = f' (last {w})'
    label = NAMES.get(base, base.replace('_', ' '))
    side = 'home' if shap_val > 0 else 'away'
    return f"{label.capitalize()}{window} favors {side}"


def main(days):
    meta = json.load(open(os.path.join(MODEL_DIR, 'game_model_meta.json')))
    model = joblib.load(os.path.join(MODEL_DIR, 'xgb_team_model.pkl'))
    conn = connect()
    up = pd.read_sql(
        "SELECT game_id, game_date, home_team_id, away_team_id FROM games "
        "WHERE status IN ('Scheduled','Live') AND game_date BETWEEN %s AND %s ORDER BY game_date",
        conn, params=(date.today() - timedelta(days=1), date.today() + timedelta(days=days)))
    if up.empty:
        print("no upcoming games")
        return
    tg = load_team_games(conn)
    ratings = {int(k): v for k, v in meta['elo'].items()}
    X, home, away = predict_features(tg, up, ratings, meta['features'])
    X = X.astype(float)
    probs = model.predict_proba(X)[:, 1]
    contribs = model.get_booster().predict(xgb.DMatrix(X), pred_contribs=True)[:, :-1]

    cur = conn.cursor()
    rows = []
    for i, gid in enumerate(X.index):
        valid = np.where(np.isnan(X.iloc[i].values), 0.0, np.abs(contribs[i]))   # no signal from missing features
        order = np.argsort(-valid)[:4]
        drivers = [describe(meta['features'][j], X.iloc[i, j], contribs[i, j]) for j in order]
        h_off, a_off = home.loc[gid, 'off_rating_r10'], away.loc[gid, 'off_rating_r10']
        h_def, a_def = home.loc[gid, 'def_rating_r10'], away.loc[gid, 'def_rating_r10']
        pace = np.nanmean([home.loc[gid, 'pace_r10'], away.loc[gid, 'pace_r10']])
        hp = (np.nanmean([h_off, a_def]) * pace / 100) if not np.isnan(pace) else None
        ap = (np.nanmean([a_off, h_def]) * pace / 100) if not np.isnan(pace) else None
        snap = {'drivers': [{'text': d, 'impact': round(float(contribs[i, j]), 3)} for d, j in zip(drivers, order)],
                'predicted_score': {'home': round(float(hp) + 1.5, 1), 'away': round(float(ap) - 1.5, 1)} if hp else None,
                'features': {k: (None if np.isnan(v) else round(float(v), 3)) for k, v in X.iloc[i].items()}}
        rows.append((gid, round(float(probs[i]), 4), round(float(1 - probs[i]), 4), '; '.join(drivers), json.dumps(snap)))
    execute_values(cur, """INSERT INTO game_predictions (game_id, model_type, predicted_at, home_win_prob, away_win_prob,
                         key_driver, feature_snapshot)
                       VALUES %s ON CONFLICT (game_id, model_type) DO UPDATE SET predicted_at=now(),
                         home_win_prob=EXCLUDED.home_win_prob, away_win_prob=EXCLUDED.away_win_prob,
                         key_driver=EXCLUDED.key_driver, feature_snapshot=EXCLUDED.feature_snapshot""",
                   rows, template="(%s,'static', now(), %s, %s, %s, %s)")
    conn.commit()
    print(f"predicted {len(X)} games")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=14)
    main(ap.parse_args().days)
