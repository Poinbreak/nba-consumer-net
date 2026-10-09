"""
GM Mode API: real rosters + contracts, a roster-strength model, CBA-style trade validation, season simulation.

State lives in the browser. The client sends `rosters` overrides ({team_id: [player_id, ...]} only for teams that
changed), so the server stays stateless and several people can play at once.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .db import REGULAR, SEASON_SQL, current_season, parallel, query, season_label
from .v2 import TEAM_COLORS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../ml'))
import roster_model as rm  # noqa: E402
from simulate_season import simulate  # noqa: E402

MODEL = json.load(open(rm.MODEL_PATH))

# Projected 2026-27 thresholds (2025-26 official values + ~7%); ONE place to edit when the league publishes them.
CAP = {'cap': 165_500_000, 'tax': 201_000_000, 'apron1': 209_700_000, 'apron2': 222_400_000,
       'label': 'Projected 2026-27 (2025-26 official +7%)'}
# Real rosters are 19-22 until the final cut-down (15 + 3 two-way in season), so cap the *offseason* ceiling here.
ROSTER_MAX, ROSTER_MIN = 21, 13

_league = {'t': 0, 'data': None}


# ── League snapshot ──────────────────────────────────────────────────────────
def _player_stats(season):
    return query(f"""
        SELECT player_id, COUNT(*) AS g, SUM(min_played)::float AS mp, SUM({rm.GAME_SCORE})::float AS gs,
               SUM(pts)::float pts, SUM(reb)::float reb, SUM(ast)::float ast
        FROM player_game_logs
        WHERE game_date >= '{season - 1}-08-01' AND game_date < '{season}-08-01'
          AND COALESCE(game_type,'Regular Season') IN {REGULAR}
        GROUP BY player_id""")


def load_league(force=False):
    """All active players with a value rating, contract and injury, plus team metadata. Cached 10 minutes."""
    if _league['data'] is not None and not force and time.time() - _league['t'] < 600:
        return _league['data']
    cs = current_season()
    players, teams, contracts, injuries = parallel(
        ("""SELECT p.player_id, p.full_name, p.position, p.age, p.team_id, p.jersey_number, p.height_in, p.headshot_url
            FROM players p WHERE p.is_active AND p.team_id IS NOT NULL""", None),
        ("""SELECT team_id, abbreviation AS abbr, full_name AS name, conference, division FROM teams
            WHERE team_id BETWEEN 1610612737 AND 1610612766 ORDER BY team_id""", None),
        ("""SELECT DISTINCT ON (player_id) player_id, salary, years_remaining, option_type, trade_restriction, season_label
            FROM contracts ORDER BY player_id, season_label DESC""", None),
        ("SELECT player_id, status FROM injuries", None),
    )
    cur_rows, prev_rows = _player_stats(cs), _player_stats(cs - 1)
    cur = {r['player_id']: r for r in cur_rows}
    prev = {r['player_id']: r for r in prev_rows}
    contracts = {r['player_id']: r for r in contracts}
    injuries = {r['player_id']: r['status'] for r in injuries}

    cols = ['g', 'mp', 'gs', 'pts', 'reb', 'ast']
    rows = []
    for p in players:
        c, v = cur.get(p['player_id']), prev.get(p['player_id'])
        # latest season at full weight, the one before at 0.6, so a returning player is not judged on 15 games
        tot = {k: (c[k] if c else 0) + 0.6 * (v[k] if v else 0) for k in cols}
        last = c or v
        rows.append({**p, **tot, 'mpg': (last['mp'] / last['g']) if last and last['g'] else 0.0,
                     'gp': (c or {}).get('g', 0), 'gp_prev': (v or {}).get('g', 0)})
    df = pd.DataFrame(rows)
    has = df['mp'] > 0
    gs36 = rm.shrunk_gs36(df['gs'].where(has, 0.0), df['mp'].where(has, 1.0), MODEL['league_mean'])
    df['value'] = gs36.where(has, MODEL['league_mean'] - MODEL['unknown_penalty'])      # rating used by the strength model
    per_game = (df['gs'] / df['g'].replace(0, np.nan)).fillna(MODEL['ovr']['mean'] - 1.0 * MODEL['ovr']['sd'])
    # thin samples regress toward a bench-level production
    games = df['g'].fillna(0)
    per_game = (per_game * games + (MODEL['ovr']['mean'] - 1.0 * MODEL['ovr']['sd']) * 8) / (games + 8)
    df['ovr'] = (MODEL['ovr']['base'] + MODEL['ovr']['scale'] * (per_game - MODEL['ovr']['mean']) / MODEL['ovr']['sd']).round().clip(40, 99).astype(int)

    by_id = {}
    for r in df.to_dict('records'):
        k = contracts.get(r['player_id'], {})
        status = injuries.get(r['player_id'])
        by_id[r['player_id']] = {
            'player_id': r['player_id'], 'name': r['full_name'], 'pos': r['position'], 'age': r['age'], 'team_id': r['team_id'],
            'headshot': r['headshot_url'], 'ovr': int(r['ovr']), 'value': float(r['value']), 'mpg': round(float(r['mpg']), 1),
            'salary': int(k.get('salary') or 0), 'years': k.get('years_remaining'), 'option': k.get('option_type') or 0,
            'locked': bool(k.get('trade_restriction')), 'injury': status,
        }
    # per-game box line for display (current season, falling back to previous)
    for pid, p in by_id.items():
        s = cur.get(pid) if cur.get(pid) and cur[pid]['g'] >= 5 else prev.get(pid)
        if s and s['g']:
            p['line'] = {'pts': round(s['pts'] / s['g'], 1), 'reb': round(s['reb'] / s['g'], 1), 'ast': round(s['ast'] / s['g'], 1)}
    rosters = {}
    for p in by_id.values():
        rosters.setdefault(p['team_id'], []).append(p['player_id'])
    data = {'players': by_id, 'rosters': rosters, 'teams': teams, 'season': cs, 'offsets': (0.0, 0.0)}
    # Re-centre so the 30 teams average a net rating of 0 and the real league-average offense (calibration shrinks toward
    # the sample mean of the backtest, which is not exactly this season's league).
    raw = [team_strength(rosters.get(t['team_id'], []), data) for t in teams]
    avg_off = query(f"SELECT AVG(off_rating)::float AS o FROM team_game_stats WHERE game_date >= '{cs - 1}-08-01' AND game_date < '{cs}-08-01' "
                    f"AND COALESCE(game_type,'Regular Season') IN {REGULAR}")[0]['o'] or 114.0
    data['offsets'] = (float(np.mean([r['off'] for r in raw])) - avg_off, float(np.mean([r['net'] for r in raw])))
    _league.update(t=time.time(), data=data)
    return data


# ── Team strength ────────────────────────────────────────────────────────────
def team_strength(player_ids, league):
    """Projected ratings for any roster. Each available player keeps about his usual minutes (rookies get 10); extra
    minutes go to the best players, excess is scaled down. Strength = minutes-weighted Game Score/36, mapped to
    off/net rating by the backtested next-season calibration (so it already regresses toward average)."""
    ps = [league['players'][i] for i in player_ids if i in league['players']]
    avail = [p for p in ps if (p['injury'] or '').lower() != 'out']
    if not avail:
        return {'off': 100.0, 'def': 115.0, 'net': -15.0, 'wins': 8.0, 'ovr': 40, 'rotation': []}
    mpg = np.array([p['mpg'] if p['mpg'] > 0 else MODEL['unknown_mpg'] for p in avail])
    val = np.array([p['value'] for p in avail])
    ovr = np.array([p['ovr'] for p in avail], float)
    mins = rm.allocate_minutes(mpg, val)
    w = mins / mins.sum()
    x = float((w * val).sum())
    cal = MODEL['calib']
    off_off, net_off = league.get('offsets', (0.0, 0.0))
    off = cal['off']['a'] + cal['off']['b'] * x - off_off
    net = cal['net']['a'] + cal['net']['b'] * x - net_off
    wins = MODEL['wins']['intercept'] + MODEL['wins']['per_net'] * net
    order = np.argsort(-mins)
    return {'off': round(off, 1), 'def': round(off - net, 1), 'net': round(net, 1), 'wins': round(wins, 1),
            'ovr': int(round(float((w * ovr).sum()))),
            'rotation': [{'player_id': avail[i]['player_id'], 'mins': round(float(mins[i]), 1)} for i in order[:10] if mins[i] >= 1]}


def apply_overrides(league, overrides):
    rosters = {int(k): list(v) for k, v in league['rosters'].items()}
    for k, v in (overrides or {}).items():
        rosters[int(k)] = [int(x) for x in v]
    return rosters


# ── CBA-style trade validation (simplified) ──────────────────────────────────
def check_side(team_name, payroll, roster_n, out_players, in_players):
    """Can this team make the trade? Returns (ok, problems, warnings, post_payroll)."""
    out_sal, in_sal = sum(p['salary'] for p in out_players), sum(p['salary'] for p in in_players)
    post = payroll - out_sal + in_sal
    problems, warnings = [], []
    for p in out_players:
        if p['locked']:
            problems.append(f"{p['name']} was recently signed and cannot be traded yet.")
    if post > CAP['cap']:        # over the cap after the trade: salary matching applies
        if post > CAP['apron2']:
            limit, rule = out_sal, "at or above the second apron a team must take back no more salary than it sends"
            if len(out_players) > 1:
                problems.append(f"{team_name}: above the second apron, salaries cannot be combined to match.")
        elif post > CAP['apron1']:
            limit, rule = 1.10 * out_sal + 100_000, "above the first apron incoming salary is capped at 110% + $0.1M"
        else:
            limit, rule = 2.00 * out_sal + 250_000, "over the cap, incoming salary is capped at 200% + $0.25M"
        if in_sal > limit:
            problems.append(f"{team_name} takes back ${in_sal / 1e6:.1f}M but may take at most ${limit / 1e6:.1f}M ({rule}).")
    n_after = roster_n - len(out_players) + len(in_players)
    if n_after > ROSTER_MAX:
        problems.append(f"{team_name} would have {n_after} players; the maximum is {ROSTER_MAX}.")
    elif n_after < ROSTER_MIN:
        warnings.append(f"{team_name} would have {n_after} players and must reach {ROSTER_MIN} before the season.")
    if post > CAP['tax'] and payroll <= CAP['tax']:
        warnings.append(f"{team_name} would cross the luxury tax line (${CAP['tax'] / 1e6:.0f}M).")
    return (not problems), problems, warnings, post


def cap_status(payroll):
    if payroll > CAP['apron2']:
        return 'Above 2nd apron'
    if payroll > CAP['apron1']:
        return 'Above 1st apron'
    if payroll > CAP['tax']:
        return 'Luxury tax'
    if payroll > CAP['cap']:
        return 'Over the cap'
    return 'Under the cap'


def _team_card(tid, league, rosters):
    t = next(t for t in league['teams'] if t['team_id'] == tid)
    ids = rosters.get(tid, [])
    payroll = sum(league['players'][i]['salary'] for i in ids if i in league['players'])
    return {**t, 'color': TEAM_COLORS.get(t['abbr'], '#8b8b95'), 'payroll': payroll, 'cap_status': cap_status(payroll),
            'roster_n': len(ids), **team_strength(ids, league)}


def _player_json(p):
    return {k: p[k] for k in ('player_id', 'name', 'pos', 'age', 'headshot', 'ovr', 'mpg', 'salary', 'years', 'option', 'locked', 'injury', 'line') if k in p}


# ── Endpoints ────────────────────────────────────────────────────────────────
@api_view(['POST', 'GET'])
def league(request):
    """Every team: payroll, cap status, projected ratings and wins for the given roster overrides."""
    lg = load_league()
    rosters = apply_overrides(lg, (request.data or {}).get('rosters') if request.method == 'POST' else None)
    return Response({'cap': CAP, 'season': season_label(lg['season'] + 1),
                     'teams': sorted([_team_card(t['team_id'], lg, rosters) for t in lg['teams']], key=lambda t: -t['wins'])})


@api_view(['POST', 'GET'])
def roster(request, team_id):
    lg = load_league()
    rosters = apply_overrides(lg, (request.data or {}).get('rosters') if request.method == 'POST' else None)
    ids = rosters.get(int(team_id), [])
    players = sorted((_player_json(lg['players'][i]) for i in ids if i in lg['players']), key=lambda p: -p['ovr'])
    return Response({'team': _team_card(int(team_id), lg, rosters), 'players': players, 'cap': CAP})


@api_view(['POST'])
def evaluate_trade(request):
    """Body: {team_a, team_b, a_gives: [ids], b_gives: [ids], rosters: {overrides}}."""
    d = request.data
    lg = load_league()
    rosters = apply_overrides(lg, d.get('rosters'))
    a, b = int(d['team_a']), int(d['team_b'])
    a_gives, b_gives = [int(x) for x in d.get('a_gives', [])], [int(x) for x in d.get('b_gives', [])]
    if not a_gives and not b_gives:
        return Response({'valid': False, 'messages': ['Pick at least one player to trade.']})
    for pid in a_gives:
        if pid not in rosters.get(a, []):
            return Response({'valid': False, 'messages': ['A selected player is no longer on that roster.']}, status=400)
    for pid in b_gives:
        if pid not in rosters.get(b, []):
            return Response({'valid': False, 'messages': ['A selected player is no longer on that roster.']}, status=400)
    P = lg['players']
    ca, cb = _team_card(a, lg, rosters), _team_card(b, lg, rosters)
    ok_a, prob_a, warn_a, post_a = check_side(ca['name'], ca['payroll'], ca['roster_n'], [P[i] for i in a_gives], [P[i] for i in b_gives])
    ok_b, prob_b, warn_b, post_b = check_side(cb['name'], cb['payroll'], cb['roster_n'], [P[i] for i in b_gives], [P[i] for i in a_gives])
    after = {k: list(v) for k, v in rosters.items()}
    after[a] = [i for i in rosters[a] if i not in a_gives] + b_gives
    after[b] = [i for i in rosters[b] if i not in b_gives] + a_gives
    na, nb = _team_card(a, lg, after), _team_card(b, lg, after)
    return Response({
        'valid': ok_a and ok_b, 'problems': prob_a + prob_b, 'warnings': warn_a + warn_b,
        'a': {'before': ca, 'after': na, 'post_payroll': post_a}, 'b': {'before': cb, 'after': nb, 'post_payroll': post_b},
        'after_rosters': {str(a): after[a], str(b): after[b]},
    })


_games_cache = {'t': 0, 'df': None}


def _remaining_games():
    if _games_cache['df'] is None or time.time() - _games_cache['t'] > 600:
        rows = query("""SELECT home_team_id, away_team_id, status, home_score, away_score FROM games
                        WHERE game_id LIKE 'E%%' ORDER BY game_date""")
        _games_cache.update(t=time.time(), df=pd.DataFrame(rows))
    return _games_cache['df']


@api_view(['POST'])
def simulate_season(request):
    """Body: {rosters: {overrides}, team_id?}. Simulates the 2026-27 schedule + playoffs from roster strength."""
    d = request.data
    lg = load_league()
    rosters = apply_overrides(lg, d.get('rosters'))
    teams = lg['teams']
    idx = {t['team_id']: i for i, t in enumerate(teams)}
    n = len(teams)
    strength = [team_strength(rosters.get(t['team_id'], []), lg) for t in teams]
    net = np.array([s['net'] for s in strength])
    rating = net * MODEL['game_logit_per_net']
    home_logit = MODEL['home_logit']
    g = _remaining_games()
    done = g[g['status'] == 'Final']
    sched = g[g['status'] != 'Final']
    h, a = sched['home_team_id'].map(idx).values, sched['away_team_id'].map(idx).values
    p = 1 / (1 + np.exp(-(rating[h] - rating[a] + home_logit)))
    base, played = np.zeros(n), np.zeros(n)
    for r in done.itertuples():
        hi, ai = idx[r.home_team_id], idx[r.away_team_id]
        base[hi if r.home_score > r.away_score else ai] += 1
        played[hi] += 1
        played[ai] += 1
    conf = np.array([t['conference'] for t in teams])
    sims = int(min(max(d.get('sims', 600), 100), 2000))
    wins, cnt, total = simulate(h, a, p, rating, conf, base, played, sims, seed=int(d.get('seed', 7)), home_logit=home_logit)
    out = []
    for t, i in idx.items():
        meta = next(x for x in teams if x['team_id'] == t)
        out.append({'team_id': t, 'abbr': meta['abbr'], 'name': meta['name'], 'conference': meta['conference'],
                    'color': TEAM_COLORS.get(meta['abbr'], '#8b8b95'), 'net': strength[i]['net'], 'off': strength[i]['off'],
                    'def': strength[i]['def'], 'exp_wins': round(float(wins[:, i].mean()), 1),
                    'p10': int(np.percentile(wins[:, i], 10)), 'p90': int(np.percentile(wins[:, i], 90)),
                    'playoffs': round(cnt['playoffs'][i] / sims, 4), 'top_seed': round(cnt['top_seed'][i] / sims, 4),
                    'finals': round(cnt['finals'][i] / sims, 4), 'title': round(cnt['title'][i] / sims, 4)})
    return Response({'sims': sims, 'teams': sorted(out, key=lambda r: -r['exp_wins'])})
