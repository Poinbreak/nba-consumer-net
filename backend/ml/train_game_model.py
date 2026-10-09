"""
Train the game-outcome model (XGBoost) with a strict time-based split.

    python ml/train_game_model.py

Walk-forward evaluation: train on all seasons before TEST_SEASON, test on TEST_SEASON.
Reports accuracy / log-loss against two baselines (always-home, Elo-only logistic) and then
refits on everything and saves xgb_team_model.pkl + game_model_meta.json.
"""
import json
import os
import sys

import joblib
import numpy as np
import xgboost as xgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss

sys.path.insert(0, os.path.dirname(__file__))
from features import build_game_features, load_team_games  # noqa: E402

MODEL_DIR = os.path.dirname(__file__)
PARAMS = dict(objective='binary:logistic', eval_metric='logloss', max_depth=3, learning_rate=0.03,
              n_estimators=400, subsample=0.8, colsample_bytree=0.6, min_child_weight=10,
              reg_lambda=5.0, random_state=42)


def main():
    X, meta, ratings, _ = build_game_features(load_team_games())
    X = X.join(meta[['season', 'home_won']])
    X = X.dropna(subset=[c for c in X.columns if c.endswith('_r10_diff')] + ['elo_diff'])
    feats = [c for c in X.columns if c not in ('season', 'home_won')]
    test_season = int(X['season'].max())
    train, test = X[X['season'] < test_season], X[X['season'] == test_season]
    print(f"{len(X)} games | features={len(feats)} | train={len(train)} | test={len(test)} (season {test_season})")

    base_home = test['home_won'].mean()
    lr = LogisticRegression().fit(train[['elo_diff']], train['home_won'])
    p_elo = lr.predict_proba(test[['elo_diff']])[:, 1]
    model = xgb.XGBClassifier(**PARAMS).fit(train[feats], train['home_won'])
    p = model.predict_proba(test[feats])[:, 1]
    y = test['home_won']
    print(f"always-home   acc={base_home:.3f}")
    print(f"elo-only      acc={accuracy_score(y, p_elo > .5):.3f}  logloss={log_loss(y, p_elo):.4f}")
    print(f"xgboost       acc={accuracy_score(y, p > .5):.3f}  logloss={log_loss(y, p):.4f}  brier={brier_score_loss(y, p):.4f}")

    final = xgb.XGBClassifier(**PARAMS).fit(X[feats], X['home_won'])
    joblib.dump(final, os.path.join(MODEL_DIR, 'xgb_team_model.pkl'))
    imp = sorted(zip(feats, final.feature_importances_), key=lambda x: -x[1])[:10]
    meta_out = {
        'features': feats, 'test_season': test_season, 'n_games': int(len(X)),
        'metrics': {'accuracy': float(accuracy_score(y, p > .5)), 'logloss': float(log_loss(y, p)),
                    'elo_accuracy': float(accuracy_score(y, p_elo > .5)), 'baseline_home': float(base_home)},
        'top_features': [(f, float(v)) for f, v in imp],
        'elo': {str(k): float(v) for k, v in ratings.items()},
    }
    with open(os.path.join(MODEL_DIR, 'game_model_meta.json'), 'w') as f:
        json.dump(meta_out, f, indent=1)
    print("top features:", [f for f, _ in imp[:6]])
    print("saved model + meta")


if __name__ == '__main__':
    main()
