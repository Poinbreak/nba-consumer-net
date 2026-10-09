"""
Shared award feature engineering. Training uses Basketball-Reference data (Kaggle: sumitrodatta/
nba-aba-baa-stats); inference uses our own player_game_logs / team_game_stats. Both sides are reduced
to the same columns (PLAYER_COLS / TEAM_COLS) so the model sees identical features either way, and
stats are z-scored within each season so different eras are comparable.
"""
import io
import os
import zipfile

import numpy as np
import pandas as pd
import requests

KAGGLE_URL = 'https://www.kaggle.com/api/v1/datasets/download/sumitrodatta/nba-aba-baa-stats'
CACHE = os.path.join(os.path.dirname(__file__), '.award_cache')
AWARDS = {'mvp': 'nba mvp', 'dpoy': 'nba dpoy', 'roy': 'nba roy', 'smoy': 'nba smoy', 'mip': 'nba mip'}
EXP_CAP = 7          # our DB only goes back to 2019, so experience is capped identically on both sides

PLAYER_COLS = ['season', 'player_key', 'name', 'team_key', 'g', 'gs', 'mp', 'pts', 'trb', 'ast', 'stl', 'blk',
               'tov', 'drb', 'fga', 'fta', 'fg', 'x3', 'ft', 'team_games']
BASE = ['pts', 'trb', 'ast', 'stl', 'blk', 'tov', 'drb', 'mpg', 'ts', 'g_frac', 'gs_pct', 'usage', 'exp',
        'team_win_pct', 'team_mov', 'team_drtg']
ZCOLS = ['pts', 'trb', 'ast', 'stl', 'blk', 'ts', 'usage', 'team_win_pct', 'team_drtg']


def kaggle_tables():
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, 'nba-aba-baa-stats.zip')
    if not os.path.exists(path):
        r = requests.get(KAGGLE_URL, timeout=300)
        r.raise_for_status()
        open(path, 'wb').write(r.content)
    z = zipfile.ZipFile(path)
    return {n[:-4]: pd.read_csv(io.BytesIO(z.read(n))) for n in z.namelist()
            if n[:-4] in ('Player Totals', 'Player Award Shares', 'Team Summaries')}


def br_player_seasons(t):
    """Basketball-Reference totals -> PLAYER_COLS (one row per player-season; TOT row for traded players)."""
    p = t['Player Totals']
    p = p[(p['lg'] == 'NBA') & (p['season'] >= 1980)].copy()
    tot = p[p['team'] == 'TOT'][['season', 'player_id']].drop_duplicates()
    traded = set(map(tuple, tot.values))
    keep = [(s, i) not in traded or tm == 'TOT' for s, i, tm in zip(p['season'], p['player_id'], p['team'])]
    p = p[keep]
    ts = t['Team Summaries']
    ts = ts[(ts['lg'] == 'NBA') & ts['abbreviation'].notna() & (ts['team'] != 'League Average')]
    games = (ts['w'] + ts['l']).groupby(ts['season']).max()
    out = pd.DataFrame({
        'season': p['season'], 'player_key': p['player_id'], 'name': p['player'],
        'team_key': np.where(p['team'] == 'TOT', None, p['team']), 'g': p['g'], 'gs': p['gs'], 'mp': p['mp'],
        'pts': p['pts'], 'trb': p['trb'], 'ast': p['ast'], 'stl': p['stl'], 'blk': p['blk'], 'tov': p['tov'],
        'drb': p['drb'], 'fga': p['fga'], 'fta': p['fta'], 'fg': p['fg'], 'x3': p['x3p'], 'ft': p['ft'],
        'team_games': p['season'].map(games),
    })
    team = pd.DataFrame({
        'season': ts['season'], 'team_key': ts['abbreviation'],
        'team_win_pct': ts['w'] / (ts['w'] + ts['l']), 'team_mov': ts['mov'], 'team_drtg': ts['d_rtg']})
    first = p.groupby('player_id')['season'].min()
    out['first_season'] = out['player_key'].map(first)
    return out, team


def build_features(players: pd.DataFrame, team: pd.DataFrame):
    """players: PLAYER_COLS + first_season. Returns (feature frame, index of the eligible pool)."""
    d = players.merge(team, on=['season', 'team_key'], how='left')
    gp = d['g'].replace(0, np.nan)
    d['mpg'] = d['mp'] / gp
    for c in ['pts', 'trb', 'ast', 'stl', 'blk', 'tov', 'drb']:
        d[c] = d[c] / gp
    d['ts'] = d['pts'] * gp / (2 * (d['fga'] + 0.44 * d['fta'])).replace(0, np.nan)
    d['g_frac'] = (d['g'] / d['team_games']).clip(upper=1)
    d['gs_pct'] = d['gs'] / gp
    d['usage'] = (d['fga'] + 0.44 * d['fta'] + d['tov'] * gp) / d['mp'].replace(0, np.nan) * 48 / gp
    d['exp'] = (d['season'] - d['first_season']).clip(0, EXP_CAP)
    # previous-season deltas (for Most Improved)
    prev = d[['season', 'player_key', 'pts', 'ast', 'trb', 'mpg']].copy()
    prev['season'] += 1
    prev = prev.rename(columns={c: f'prev_{c}' for c in ['pts', 'ast', 'trb', 'mpg']})
    d = d.merge(prev, on=['season', 'player_key'], how='left')
    for c in ['pts', 'ast', 'trb', 'mpg']:
        d[f'd_{c}'] = d[c] - d[f'prev_{c}']
    pool = d[(d['mpg'] >= 12) & (d['g_frac'] >= 0.25)]
    for c in ZCOLS:
        mu, sd = pool.groupby('season')[c].mean(), pool.groupby('season')[c].std()
        d[f'{c}_z'] = (d[c] - d['season'].map(mu)) / d['season'].map(sd)
    d['pts_rank'] = pool.groupby('season')['pts'].rank(ascending=False).reindex(d.index)
    d['comp_z'] = d['pts_z'] + d['trb_z'] + d['ast_z']
    return d, pool.index


FEATS = BASE + [f'{c}_z' for c in ZCOLS] + ['pts_rank', 'comp_z', 'd_pts', 'd_ast', 'd_trb', 'd_mpg', 'prev_pts']


def award_pool(d: pd.DataFrame, award: str):
    m = (d['mpg'] >= 12) & (d['g_frac'] >= 0.25)
    if award == 'roy':
        m &= d['exp'] == 0
    elif award == 'smoy':
        m &= (d['gs_pct'] <= 0.5) & (d['mpg'] >= 15)
    elif award == 'mip':
        m &= d['exp'] >= 1
    return d[m]
