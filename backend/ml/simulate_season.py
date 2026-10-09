"""
Monte Carlo season simulator: win totals, playoff/play-in odds and title odds per team.

Single-game probabilities come from game_predictions (the XGBoost game model). Team strengths for
playoff series are backed out of those same probabilities (least squares on the logit scale), so the
whole projection is consistent with the model.

    python ml/simulate_season.py [--sims 5000]
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
from psycopg2.extras import execute_values

sys.path.insert(0, os.path.dirname(__file__))
from features import connect  # noqa: E402

HOME_LOGIT = 0.30     # ~57% home edge between equal teams; observed league-wide is 55.5-58%


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def fit_ratings(sched, n):
    """logit(p_home) = r_home - r_away + HOME_LOGIT, solved by least squares, mean-centered."""
    A = np.zeros((len(sched), n))
    A[np.arange(len(sched)), sched['h'].values] = 1
    A[np.arange(len(sched)), sched['a'].values] -= 1
    p = sched['p'].astype(float).clip(0.02, 0.98).values
    y = np.log(p / (1 - p)) - HOME_LOGIT
    r, *_ = np.linalg.lstsq(A, y, rcond=None)
    return r - r.mean()


def series_table(r):
    """S[a, b] = P(a wins a best-of-7 | a has home court), home pattern HHAAHAH."""
    n = len(r)
    home_pattern = [1, 1, 0, 0, 1, 0, 1]
    S = np.zeros((n, n))
    for a in range(n):
        for b in range(n):
            if a == b:
                continue
            pa_home, pa_away = sigmoid(r[a] - r[b] + HOME_LOGIT), sigmoid(r[a] - r[b] - HOME_LOGIT)
            dp, win = {(0, 0): 1.0}, 0.0
            for gm in range(7):
                p = pa_home if home_pattern[gm] else pa_away
                nxt = {}
                for (wa, wb), pr in dp.items():
                    nxt[(wa + 1, wb)] = nxt.get((wa + 1, wb), 0) + pr * p
                    nxt[(wa, wb + 1)] = nxt.get((wa, wb + 1), 0) + pr * (1 - p)
                win += sum(v for k, v in nxt.items() if k[0] == 4)
                dp = {k: v for k, v in nxt.items() if 4 not in k}
            S[a, b] = win
    return S


def main(sims):
    conn = connect()
    g = pd.read_sql("""SELECT g.game_id, g.game_date, g.home_team_id, g.away_team_id, g.status,
                              g.home_score, g.away_score, p.home_win_prob AS p
                       FROM games g LEFT JOIN game_predictions p ON p.game_id = g.game_id AND p.model_type = 'static'
                       WHERE g.game_id LIKE 'E%%' ORDER BY g.game_date""", conn)
    teams = pd.read_sql("""SELECT team_id, abbreviation, conference FROM teams
                           WHERE team_id BETWEEN 1610612737 AND 1610612766 ORDER BY team_id""", conn)
    idx = {t: i for i, t in enumerate(teams['team_id'])}
    n = len(teams)
    g['h'], g['a'] = g['home_team_id'].map(idx), g['away_team_id'].map(idx)
    done = g[g['status'] == 'Final']
    sched = g[(g['status'] != 'Final') & g['p'].notna()].reset_index(drop=True)
    if sched.empty:
        print("nothing to simulate")
        return
    base, played = np.zeros(n), np.zeros(n)
    for r in done.itertuples():
        base[r.h if r.home_score > r.away_score else r.a] += 1
        played[r.h] += 1
        played[r.a] += 1

    rating = fit_ratings(sched, n)
    S = series_table(rating)

    def game_p(a, b):             # a hosts b
        return sigmoid(rating[a] - rating[b] + HOME_LOGIT)

    rng = np.random.default_rng(42)
    G = len(sched)
    outcome = rng.random((sims, G)) < sched['p'].astype(float).values[None, :]
    Hm, Am = np.zeros((G, n)), np.zeros((G, n))
    Hm[np.arange(G), sched['h'].values] = 1
    Am[np.arange(G), sched['a'].values] = 1
    wins = base[None, :] + outcome @ Hm + (~outcome) @ Am
    total_games = played + Hm.sum(0) + Am.sum(0)
    # ESPN publishes the tail of the schedule late: fill each team's missing games vs an average opponent
    missing = np.clip(82 - total_games, 0, None).astype(int)
    for i in range(n):
        if missing[i]:
            wins[:, i] += rng.binomial(missing[i], sigmoid(rating[i]), size=sims)
    total_games = total_games + missing

    conf = teams['conference'].values
    groups = (np.where(conf == 'East')[0], np.where(conf == 'West')[0])
    cnt = {k: np.zeros(n) for k in ('playoffs', 'top_seed', 'conf_finals', 'finals', 'title')}

    def play_game(a, b):
        return a if rng.random() < game_p(a, b) else b

    def series(a, b, w):          # more regular-season wins = home court
        hi, lo = (a, b) if w[a] >= w[b] else (b, a)
        return hi if rng.random() < S[hi, lo] else lo

    for s in range(sims):
        w = wins[s] + rng.random(n) * 0.01      # random tiebreak
        champs = []
        for grp in groups:
            order = grp[np.argsort(-w[grp])]
            cnt['top_seed'][order[0]] += 1
            s7, s8, s9, s10 = order[6], order[7], order[8], order[9]
            w78 = play_game(s7, s8)
            l78 = s8 if w78 == s7 else s7
            seeds = list(order[:6]) + [w78, play_game(l78, play_game(s9, s10))]
            for t in seeds:
                cnt['playoffs'][t] += 1
            r1 = [series(seeds[0], seeds[7], w), series(seeds[3], seeds[4], w),
                  series(seeds[2], seeds[5], w), series(seeds[1], seeds[6], w)]
            r2 = [series(r1[0], r1[1], w), series(r1[2], r1[3], w)]
            for t in r2:
                cnt['conf_finals'][t] += 1
            champs.append(series(r2[0], r2[1], w))
        for t in champs:
            cnt['finals'][t] += 1
        cnt['title'][series(champs[0], champs[1], w)] += 1

    exp_w = wins.mean(0)
    cur = conn.cursor()
    cur.execute("SELECT MIN(game_date) FROM games WHERE game_id LIKE 'E%%'")
    y = cur.fetchone()[0].year
    label = f"{y}-{str(y + 1)[2:]}"
    rows = []
    for t_id, i in idx.items():
        rows.append((label, t_id, round(float(exp_w[i]), 2), round(float(total_games[i] - exp_w[i]), 2),
                     int(np.percentile(wins[:, i], 10)), int(np.percentile(wins[:, i], 90)),
                     round(cnt['playoffs'][i] / sims, 4), round(cnt['top_seed'][i] / sims, 4),
                     round(cnt['conf_finals'][i] / sims, 4), round(cnt['finals'][i] / sims, 4),
                     round(cnt['title'][i] / sims, 4), round(float(rating[i]), 3), sims))
    rows = [tuple(x.item() if hasattr(x, 'item') else x for x in r) for r in rows]
    execute_values(cur, """INSERT INTO season_projections (season_label, team_id, exp_wins, exp_losses, p10th_wins,
                             p90th_wins, playoff_prob, top_seed_prob, conf_finals_prob, finals_prob, title_prob,
                             rating, sims, updated_at) VALUES %s
                           ON CONFLICT (season_label, team_id) DO UPDATE SET exp_wins=EXCLUDED.exp_wins,
                             exp_losses=EXCLUDED.exp_losses, p10th_wins=EXCLUDED.p10th_wins,
                             p90th_wins=EXCLUDED.p90th_wins, playoff_prob=EXCLUDED.playoff_prob,
                             top_seed_prob=EXCLUDED.top_seed_prob, conf_finals_prob=EXCLUDED.conf_finals_prob,
                             finals_prob=EXCLUDED.finals_prob, title_prob=EXCLUDED.title_prob,
                             rating=EXCLUDED.rating, sims=EXCLUDED.sims, updated_at=now()""",
                   rows, template="(" + ",".join(["%s"] * 13) + ", now())")
    conn.commit()
    out = pd.DataFrame(rows, columns=['season', 'team_id', 'w', 'l', 'p10', 'p90', 'playoffs', 'top', 'cf', 'fin',
                                      'title', 'r', 's'])
    out['team'] = teams['abbreviation'].values
    print(out.sort_values('title', ascending=False).head(10)[
        ['team', 'w', 'p10', 'p90', 'playoffs', 'cf', 'fin', 'title']].to_string(index=False))
    print(f"title odds sum={out['title'].sum():.3f}  mean wins={out['w'].mean():.1f}  ({label}, {sims} sims)")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--sims', type=int, default=5000)
    main(ap.parse_args().sims)
