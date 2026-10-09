"""
Roster -> team strength model, used by GM Mode.

One number per player: Game Score per 36 minutes (Hollinger's box-score production formula), shrunk toward the league
mean for small samples. A team's strength is the minutes-weighted average of its players' ratings. We fit the mapping
from that average to team offensive / net rating by projecting each team-season from its players' PRIOR-season stats,
so the calibration already includes the regression to the mean that any next-season projection needs.

(An 8-feature ridge model fit better in-season but worse out of sample, 0.46 vs 0.52 correlation with next-season net
rating, so the simple model won.)

    python ml/roster_model.py     # backtest + fit, writes roster_model.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression

sys.path.insert(0, os.path.dirname(__file__))
from features import connect  # noqa: E402

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'roster_model.json')
REGULAR = "('Regular Season','NBA Emirates Cup')"
SEASON = "(EXTRACT(YEAR FROM (game_date - INTERVAL '6 months'))::int + 1)"
K_SHRINK = 400.0        # minutes of league-average play blended into every player (small samples)
UNKNOWN_MPG = 10.0      # rookies / players with no NBA minutes
UNKNOWN_PENALTY = 1.0   # ...and they are rated this far below the average rotation player (Game Score per 36)
GAME_SCORE = "pts + 0.4*fgm - 0.7*fga - 0.4*(fta-ftm) + 0.7*oreb + 0.3*dreb + stl + 0.7*ast + 0.7*blk - 0.4*pf - tov"


def allocate_minutes(mpg, value, total=240.0, cap=38.0):
    """Players keep roughly their usual minutes; when the roster has too many/few minutes, scale down proportionally
    or hand the shortfall to the most valuable players (up to `cap`). mpg/value: arrays aligned per player."""
    m = np.clip(np.asarray(mpg, float), 0, cap).copy()
    if m.sum() > total:
        return m * (total / m.sum())
    deficit = total - m.sum()
    for i in np.argsort(-np.asarray(value, float)):
        add = min(cap - m[i], deficit)
        m[i] += add
        deficit -= add
        if deficit <= 1e-9:
            break
    return m


def shrunk_gs36(gs, mp, league_mean):
    """Game Score per 36 min, blended toward the league mean with weight K_SHRINK minutes."""
    return (gs / mp * 36 * mp + league_mean * K_SHRINK) / (mp + K_SHRINK)


def fit():
    conn = connect()
    pts = pd.read_sql(f"""
        SELECT {SEASON} AS season, team_id, player_id, COUNT(*) AS g, SUM(min_played)::float AS mp,
               SUM({GAME_SCORE})::float AS gs
        FROM player_game_logs WHERE COALESCE(game_type,'Regular Season') IN {REGULAR} GROUP BY 1, 2, 3""", conn)
    teams = pd.read_sql(f"""
        SELECT {SEASON} AS season, team_id, COUNT(*) AS g, SUM(win::int) AS wins,
               AVG(off_rating)::float AS off, AVG(net_rating)::float AS net
        FROM team_game_stats WHERE COALESCE(game_type,'Regular Season') IN {REGULAR}
        GROUP BY 1, 2 HAVING COUNT(*) >= 50""", conn).set_index(['season', 'team_id'])
    pts = pts[pts['mp'] > 0].reset_index(drop=True)
    by_ps = pts.groupby(['season', 'player_id'])[['g', 'mp', 'gs']].sum()
    league_mean = float((by_ps['gs'] / by_ps['mp'] * 36)[by_ps['mp'] >= 300].mean())
    by_ps['val'] = shrunk_gs36(by_ps['gs'], by_ps['mp'], league_mean)
    by_ps['mpg'] = by_ps['mp'] / by_ps['g']

    # Next-season projection backtest: players who actually played for the team, described by PRIOR-season stats.
    rows = []
    for (s, t), g in pts[pts['g'] >= 10].groupby(['season', 'team_id']):
        if (s, t) not in teams.index or s < 2021:
            continue
        vals, mpgs = [], []
        for pid in g['player_id']:
            k = (s - 1, pid)
            if k in by_ps.index:
                vals.append(by_ps.loc[k, 'val']); mpgs.append(min(by_ps.loc[k, 'mpg'], 38.0))
            else:
                vals.append(league_mean - UNKNOWN_PENALTY); mpgs.append(UNKNOWN_MPG)
        mins = allocate_minutes(np.array(mpgs), np.array(vals))
        rows.append((s, t, float((np.array(vals) * mins / mins.sum()).sum()), teams.loc[(s, t), 'net'], teams.loc[(s, t), 'off'],
                     teams.loc[(s, t), 'wins'] / teams.loc[(s, t), 'g'] * 82))
    R = pd.DataFrame(rows, columns=['season', 'team', 'x', 'net', 'off', 'wins'])
    model = {'league_mean': league_mean, 'k_shrink': K_SHRINK, 'unknown_mpg': UNKNOWN_MPG, 'unknown_penalty': UNKNOWN_PENALTY,
             'calib': {}, 'backtest': {}}
    print(f"{len(R)} team-seasons projected from prior-season player stats")
    for t in ('net', 'off'):
        c = float(np.corrcoef(R['x'], R[t])[0, 1])
        slope, icpt = np.polyfit(R['x'], R[t], 1)
        cv = pd.Series(index=R.index, dtype=float)      # leave-one-season-out R2 of the linear map
        for s in R['season'].unique():
            m = LinearRegression().fit(R.loc[R['season'] != s, ['x']], R.loc[R['season'] != s, t])
            cv.loc[R['season'] == s] = m.predict(R.loc[R['season'] == s, ['x']])
        r2 = 1 - ((R[t] - cv) ** 2).sum() / ((R[t] - R[t].mean()) ** 2).sum()
        model['calib'][t] = {'a': float(icpt), 'b': float(slope)}
        model['backtest'][t] = {'corr': c, 'loso_r2': float(r2)}
        print(f"  {t:3s}: corr {c:.3f}, leave-season-out R2 {r2:.3f};  {t} = {icpt:+.1f} + {slope:.2f} x (minutes-weighted Game Score/36)")
    w = LinearRegression().fit(teams[['net']], teams['wins'] / teams['g'] * 82)
    model['wins'] = {'intercept': float(w.intercept_), 'per_net': float(w.coef_[0])}
    print(f"  wins = {w.intercept_:.1f} + {w.coef_[0]:.2f} x net")

    gm = pd.read_sql(f"""
        SELECT {SEASON.replace('game_date', 'h.game_date')} AS season, h.team_id AS hid, a.team_id AS aid, (h.win)::int AS home_won
        FROM team_game_stats h JOIN team_game_stats a ON a.game_id = h.game_id AND a.team_id <> h.team_id
        WHERE h.is_home AND COALESCE(h.game_type,'Regular Season') IN {REGULAR}""", conn)
    net = teams['net']
    gm['d'] = [net.get((s, h), np.nan) - net.get((s, a), np.nan) for s, h, a in zip(gm['season'], gm['hid'], gm['aid'])]
    gm = gm.dropna()
    lg = LogisticRegression(C=100).fit(gm[['d']], gm['home_won'])
    model['game_logit_per_net'], model['home_logit'] = float(lg.coef_[0][0]), float(lg.intercept_[0])
    print(f"  game win logit = {lg.intercept_[0]:.2f} + {lg.coef_[0][0]:.3f} x net diff")

    # OVR scale: season production per game (Game Score/game) among real rotation players of the latest season
    last = int(by_ps.index.get_level_values(0).max())
    cur = by_ps.xs(last, level='season')
    elig = cur[(cur['mpg'] >= 15) & (cur['g'] >= 20)]
    per_game = elig['gs'] / elig['g']
    model['ovr'] = {'mean': float(per_game.mean()), 'sd': float(per_game.std()), 'base': 68.0, 'scale': 8.0}
    print(f"  OVR scale from {last}: mean {per_game.mean():.1f} Game Score/game, sd {per_game.std():.1f}, n={len(elig)}")
    json.dump(model, open(MODEL_PATH, 'w'), indent=1)
    print('saved', MODEL_PATH)


if __name__ == '__main__':
    fit()
