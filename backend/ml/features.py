"""
Point-in-time feature builder for game outcome models.

Every feature for a game uses only information available BEFORE tipoff (rolling windows are
shifted by one game; Elo is read before it is updated), so training has no look-ahead leakage.
"""
import os

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

ROLL_COLS = ['off_rating', 'def_rating', 'net_rating', 'efg_pct', 'tov_pct', 'oreb_pct', 'ft_rate', 'pace', 'fga']
WINDOWS = (5, 10, 20)
ELO_K, ELO_HOME, ELO_CARRY = 20.0, 70.0, 0.75


def connect():
    """DATABASE_URL (pooler URI, works from IPv4-only CI) wins; else discrete SUPABASE_DB_* vars."""
    if os.environ.get('DATABASE_URL'):
        return psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
    return psycopg2.connect(
        host=os.environ['SUPABASE_DB_HOST'], port=os.environ['SUPABASE_DB_PORT'],
        dbname=os.environ['SUPABASE_DB_NAME'], user=os.environ.get('SUPABASE_DB_USER', 'postgres'),
        password=os.environ['SUPABASE_DB_PASSWORD'], sslmode='require',
    )


def load_team_games(conn=None):
    conn = conn or connect()
    df = pd.read_sql(
        "SELECT game_id, team_id, opp_team_id, is_home, win, game_date, game_type, pts, opp_pts, "
        + ", ".join(ROLL_COLS) + " FROM team_game_stats ORDER BY game_date, game_id", conn)
    df['game_date'] = pd.to_datetime(df['game_date'])
    for c in ROLL_COLS + ['pts', 'opp_pts']:
        df[c] = df[c].astype(float)
    return df


def add_team_form(tg: pd.DataFrame) -> pd.DataFrame:
    """Rolling pre-game form, rest days and season win%, per team."""
    tg = tg.sort_values(['team_id', 'game_date', 'game_id']).copy()
    g = tg.groupby('team_id', group_keys=False)
    for w in WINDOWS:
        for c in ROLL_COLS:
            tg[f'{c}_r{w}'] = g[c].transform(lambda s: s.shift(1).rolling(w, min_periods=max(3, w // 2)).mean())
    prev = g['game_date'].shift(1)
    tg['rest_days'] = (tg['game_date'] - prev).dt.days.clip(upper=7).fillna(7)
    tg['games_last7'] = g['game_date'].transform(
        lambda s: s.apply(lambda d: ((s < d) & (s >= d - pd.Timedelta(days=7))).sum()))
    # season = Oct..Jun; assign by shifting 6 months back
    tg['season'] = (tg['game_date'] - pd.DateOffset(months=6)).dt.year
    tg['win_i'] = tg['win'].astype(float)
    sg = tg.groupby(['team_id', 'season'])['win_i']
    tg['season_win_pct'] = sg.transform(lambda s: s.shift(1).expanding().mean())
    tg['season_games'] = sg.cumcount()
    return tg


def compute_elo(games: pd.DataFrame):
    """games: one row per game with home_team_id, away_team_id, home_pts, away_pts, game_date sorted.
    Returns (pre-game home elo, pre-game away elo, final ratings dict)."""
    ratings, last_season = {}, None
    h_pre, a_pre = [], []
    for r in games.itertuples():
        if last_season is not None and r.season != last_season:
            ratings = {t: 1500 + ELO_CARRY * (e - 1500) for t, e in ratings.items()}
        last_season = r.season
        he, ae = ratings.get(r.home_team_id, 1500.0), ratings.get(r.away_team_id, 1500.0)
        h_pre.append(he)
        a_pre.append(ae)
        exp_h = 1 / (1 + 10 ** (-(he + ELO_HOME - ae) / 400))
        margin = r.home_pts - r.away_pts
        res = 1.0 if margin > 0 else 0.0
        mult = np.log(abs(margin) + 1) * (2.2 / ((abs(he - ae) * 0.001) + 2.2))
        delta = ELO_K * mult * (res - exp_h)
        ratings[r.home_team_id], ratings[r.away_team_id] = he + delta, ae - delta
    return np.array(h_pre), np.array(a_pre), ratings


FORM_FEATS = [f'{c}_r{w}' for w in WINDOWS for c in ROLL_COLS] + ['rest_days', 'games_last7', 'season_win_pct']


def build_game_features(tg: pd.DataFrame):
    """Returns (one row per completed game with diff features + home_won, final elo ratings)."""
    tg = add_team_form(tg)
    home = tg[tg['is_home']].set_index('game_id')
    away = tg[~tg['is_home']].set_index('game_id')
    idx = home.index.intersection(away.index)
    home, away = home.loc[idx], away.loc[idx]

    games = pd.DataFrame({
        'game_date': home['game_date'], 'season': home['season'], 'game_type': home['game_type'],
        'home_team_id': home['team_id'], 'away_team_id': away['team_id'],
        'home_pts': home['pts'], 'away_pts': away['pts'],
    }).sort_values(['game_date']).reset_index()
    h_elo, a_elo, ratings = compute_elo(games)
    games['home_elo'], games['away_elo'] = h_elo, a_elo
    games = games.set_index('game_id')

    X = pd.DataFrame(index=games.index)
    X['elo_diff'] = games['home_elo'] - games['away_elo'] + ELO_HOME
    for f in FORM_FEATS:
        X[f'{f}_diff'] = home[f].reindex(games.index) - away[f].reindex(games.index)
    X['home_rest'] = home['rest_days'].reindex(games.index)
    X['away_rest'] = away['rest_days'].reindex(games.index)
    X['home_b2b'] = (X['home_rest'] <= 1).astype(int)
    X['away_b2b'] = (X['away_rest'] <= 1).astype(int)
    X['is_playoffs'] = (games['game_type'] == 'Playoffs').astype(int)
    meta = games[['game_date', 'season', 'home_team_id', 'away_team_id', 'home_pts', 'away_pts']].copy()
    meta['home_won'] = (meta['home_pts'] > meta['away_pts']).astype(int)
    return X, meta, ratings, tg


def predict_features(tg: pd.DataFrame, upcoming: pd.DataFrame, ratings: dict, feature_names):
    """Features for scheduled games. `upcoming`: game_id, game_date, home_team_id, away_team_id.
    Scheduled games are appended as stat-less placeholder rows, so shifted rolling windows see only
    games already played."""
    upcoming = upcoming.copy()
    upcoming['game_date'] = pd.to_datetime(upcoming['game_date'])
    rows = []
    for r in upcoming.itertuples():
        rows.append(dict(game_id=r.game_id, team_id=r.home_team_id, opp_team_id=r.away_team_id, is_home=True, game_date=r.game_date))
        rows.append(dict(game_id=r.game_id, team_id=r.away_team_id, opp_team_id=r.home_team_id, is_home=False, game_date=r.game_date))
    ph = pd.DataFrame(rows)
    ph['game_type'] = 'Regular Season'
    full = add_team_form(pd.concat([tg, ph], ignore_index=True))
    full = full[full['game_id'].isin(upcoming['game_id'])]
    home = full[full['is_home']].set_index('game_id')
    away = full[~full['is_home']].set_index('game_id')
    up = upcoming.set_index('game_id')
    last_done = tg['game_date'].max()
    new_season = (up['game_date'].min() - pd.DateOffset(months=6)).year != (last_done - pd.DateOffset(months=6)).year
    elo = {t: (1500 + ELO_CARRY * (e - 1500) if new_season else e) for t, e in ratings.items()}
    X = pd.DataFrame(index=up.index)
    X['elo_diff'] = [elo.get(h, 1500.0) - elo.get(a, 1500.0) + ELO_HOME
                     for h, a in zip(up['home_team_id'], up['away_team_id'])]
    for f in FORM_FEATS:
        X[f'{f}_diff'] = home[f].reindex(up.index) - away[f].reindex(up.index)
    X['home_rest'] = home['rest_days'].reindex(up.index)
    X['away_rest'] = away['rest_days'].reindex(up.index)
    X['home_b2b'] = (X['home_rest'] <= 1).astype(int)
    X['away_b2b'] = (X['away_rest'] <= 1).astype(int)
    X['is_playoffs'] = 0
    return X[feature_names], home, away
