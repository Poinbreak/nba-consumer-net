"""
Train award-share models (MVP, DPOY, ROY, 6MOY, MIP) on Basketball-Reference voting history.

    python ml/train_awards.py

Backtest: train on seasons <= 2019, score 2020-2025 (hit = predicted #1 is the actual winner).
Final models are refit on every season and saved to awards_<name>.pkl; metrics -> awards_meta.json.
"""
import json
import os
import sys

import joblib
import pandas as pd
import xgboost as xgb

sys.path.insert(0, os.path.dirname(__file__))
from award_features import AWARDS, FEATS, award_pool, br_player_seasons, build_features, kaggle_tables  # noqa: E402

MODEL_DIR = os.path.dirname(__file__)
TEST_FROM = 2020
PARAMS = dict(objective='reg:squarederror', max_depth=3, learning_rate=0.05, n_estimators=300,
              subsample=0.8, colsample_bytree=0.8, min_child_weight=3, random_state=7)


def dataset():
    t = kaggle_tables()
    players, team = br_player_seasons(t)
    d, _ = build_features(players, team)
    d['player_id'] = d['player_key']
    shares = t['Player Award Shares']
    out = {}
    for key, award in AWARDS.items():
        s = shares[shares['award'] == award][['season', 'player_id', 'share', 'winner']]
        m = award_pool(d, key)
        m = m[m['season'] <= s['season'].max()]          # seasons after the last labeled vote are unlabeled, not 'no winner'
        m = m.merge(s, on=['season', 'player_id'], how='left')
        m['share'] = m['share'].fillna(0.0)
        m['winner'] = m['winner'].fillna(False).astype(bool)
        out[key] = m
    return out


def main():
    meta = {}
    for key, df in dataset().items():
        df = df[df['season'] >= 1985]
        tr, te = df[df['season'] < TEST_FROM], df[df['season'] >= TEST_FROM]
        model = xgb.XGBRegressor(**PARAMS).fit(tr[FEATS], tr['share'])
        te = te.assign(pred=model.predict(te[FEATS]))
        top1 = top3 = n = 0
        for _, g in te.groupby('season'):
            if not g['winner'].any():
                continue
            n += 1
            ranked = g.sort_values('pred', ascending=False)
            top1 += bool(ranked.iloc[0]['winner'])
            top3 += bool(ranked.head(3)['winner'].any())
        print(f"{key:5s} seasons={n}  winner@1={top1}/{n}  winner@top3={top3}/{n}  "
              f"train_rows={len(tr)}  e.g. {te[te['season'] == te['season'].max()].nlargest(1, 'pred')['name'].iloc[0]}")
        final = xgb.XGBRegressor(**PARAMS).fit(df[FEATS], df['share'])
        joblib.dump(final, os.path.join(MODEL_DIR, f'awards_{key}.pkl'))
        meta[key] = {'backtest_seasons': n, 'winner_at_1': top1, 'winner_in_top3': top3, 'rows': int(len(df))}
    meta['features'] = FEATS
    json.dump(meta, open(os.path.join(MODEL_DIR, 'awards_meta.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
