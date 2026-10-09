"""
Sync schedule, live scores and final box scores from ESPN's public JSON API into Postgres.

ESPN is used because cdn.nba.com / stats.nba.com block cloud IPs (GitHub Actions included).
New-season games are stored with game_id = 'E' + espn_event_id so they never collide with the
Kaggle NBA ids already in the table.

    python scripts/sync_scores.py [--back 3] [--ahead 14] [--season-from 2026-10-01 --season-to 2027-06-30]
"""
import argparse
import os
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../ml'))
from features import connect  # noqa: E402

BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/'
ESPN_ABBR = {'GS': 'GSW', 'NY': 'NYK', 'SA': 'SAS', 'NO': 'NOP', 'UTAH': 'UTA', 'WSH': 'WAS'}
STATUS = {'STATUS_SCHEDULED': 'Scheduled', 'STATUS_IN_PROGRESS': 'Live', 'STATUS_HALFTIME': 'Live',
          'STATUS_END_PERIOD': 'Live', 'STATUS_FINAL': 'Final', 'STATUS_POSTPONED': 'Scheduled'}


def get(path, **params):
    r = requests.get(BASE + path, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def norm(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z ]', '', re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', s)).strip()


def team_map(cur):
    cur.execute("SELECT abbreviation, team_id FROM teams WHERE team_id BETWEEN 1610612737 AND 1610612766")
    m = {a: t for a, t in cur.fetchall()}
    m['SAS'] = m.get('SAS') or m.get('SAN')
    return m


def to_int(x, default=0):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return default


def pair(s):
    a, _, b = (s or '0-0').partition('-')
    return to_int(a), to_int(b)


def sync_games(cur, tmap, start: date, end: date):
    n, finals = 0, []
    d = start
    while d <= end:
        try:
            events = get('scoreboard', dates=d.strftime('%Y%m%d')).get('events', [])
        except requests.RequestException as e:
            print(f"  {d}: scoreboard failed ({e})")
            d += timedelta(days=1)
            continue
        for e in events:
            stype = (e.get('season') or {}).get('type')
            if stype == 1:      # preseason: not representative, keep out of stats
                continue
            comp = e['competitions'][0]
            c = {x['homeAway']: x for x in comp['competitors']}
            ids = [tmap.get(ESPN_ABBR.get(c[k]['team']['abbreviation'], c[k]['team']['abbreviation'])) for k in ('home', 'away')]
            if None in ids:
                continue
            st = STATUS.get(comp['status']['type']['name'], 'Scheduled')
            gid = 'E' + e['id']
            gdate = datetime.fromisoformat(e['date'].replace('Z', '+00:00')).astimezone(timezone(timedelta(hours=-5))).date()
            live = st == 'Live'
            cur.execute("""
                INSERT INTO games (game_id, game_date, home_team_id, away_team_id, home_score, away_score,
                                   status, quarter, time_remaining)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (game_id) DO UPDATE SET game_date=EXCLUDED.game_date, home_score=EXCLUDED.home_score,
                    away_score=EXCLUDED.away_score, status=EXCLUDED.status, quarter=EXCLUDED.quarter,
                    time_remaining=EXCLUDED.time_remaining""",
                (gid, gdate, ids[0], ids[1],
                 to_int(c['home'].get('score')) if st != 'Scheduled' else None,
                 to_int(c['away'].get('score')) if st != 'Scheduled' else None,
                 st, comp['status']['period'] if live else None, comp['status']['displayClock'] if live else None))
            n += 1
            if st == 'Final':
                finals.append((gid, e['id'], gdate, comp['competitors'], c, stype))
        d += timedelta(days=1)
    print(f"games upserted: {n}")
    return finals


def ratings(pts, opp_pts, fga, fta, oreb, tov, o_fga, o_fta, o_oreb, o_tov):
    poss = fga + 0.44 * fta - oreb + tov
    o_poss = o_fga + 0.44 * o_fta - o_oreb + o_tov
    avg = (poss + o_poss) / 2 or 1
    return 100 * pts / avg, 100 * opp_pts / avg, avg


def sync_box_scores(cur, finals, tmap):
    cur.execute("SELECT p.full_name, p.player_id FROM players p ORDER BY EXISTS (SELECT 1 FROM player_game_logs l WHERE l.player_id = p.player_id AND l.game_date > '2025-01-01')")
    pmap = {norm(n): i for n, i in cur.fetchall()}
    done = 0
    for gid, eid, gdate, comps, c, stype in finals:
        cur.execute("SELECT 1 FROM team_game_stats WHERE game_id=%s LIMIT 1", (gid,))
        if cur.fetchone():
            continue
        try:
            s = get('summary', event=eid)
        except requests.RequestException:
            continue
        teams = {}
        for t in s['boxscore']['teams']:
            st = {x['name']: x['displayValue'] for x in t['statistics']}
            fgm, fga = pair(st.get('fieldGoalsMade-fieldGoalsAttempted'))
            tpm, tpa = pair(st.get('threePointFieldGoalsMade-threePointFieldGoalsAttempted'))
            ftm, fta = pair(st.get('freeThrowsMade-freeThrowsAttempted'))
            abbr = ESPN_ABBR.get(t['team']['abbreviation'], t['team']['abbreviation'])
            teams[t['homeAway']] = dict(
                team_id=tmap[abbr], fgm=fgm, fga=fga, fg3m=tpm, fg3a=tpa, ftm=ftm, fta=fta,
                reb=to_int(st.get('totalRebounds')), oreb=to_int(st.get('offensiveRebounds')),
                dreb=to_int(st.get('defensiveRebounds')), ast=to_int(st.get('assists')),
                stl=to_int(st.get('steals')), blk=to_int(st.get('blocks')),
                tov=to_int(st.get('totalTurnovers') or st.get('turnovers')), pf=to_int(st.get('fouls')),
                pts_fb=to_int(st.get('fastBreakPoints')), pts_paint=to_int(st.get('pointsInPaint')))
        if set(teams) != {'home', 'away'}:
            continue
        for side, opp in (('home', 'away'), ('away', 'home')):
            me, ot = teams[side], teams[opp]
            comp = c[side]
            pts, opp_pts = to_int(comp.get('score')), to_int(c[opp].get('score'))
            q = [to_int(l['value']) for l in comp.get('linescores', [])][:4] + [None] * 4
            off, deff, poss = ratings(pts, opp_pts, me['fga'], me['fta'], me['oreb'], me['tov'],
                                      ot['fga'], ot['fta'], ot['oreb'], ot['tov'])
            fga1 = me['fga'] or 1
            cur.execute("""
                INSERT INTO team_game_stats (game_id, team_id, opp_team_id, is_home, win, pts, opp_pts, reb, ast, stl, blk,
                    tov, fgm, fga, fg3m, fg3a, ftm, fta, fg_pct, fg3_pct, ft_pct, oreb, dreb, pf, pts_fb, pts_paint,
                    plus_minus, efg_pct, tov_pct, oreb_pct, ft_rate, off_rating, def_rating, net_rating, pace,
                    q1_pts, q2_pts, q3_pts, q4_pts, game_date, game_type)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (game_id, team_id) DO NOTHING""",
                (gid, me['team_id'], ot['team_id'], side == 'home', pts > opp_pts, pts, opp_pts, me['reb'], me['ast'],
                 me['stl'], me['blk'], me['tov'], me['fgm'], me['fga'], me['fg3m'], me['fg3a'], me['ftm'], me['fta'],
                 round(me['fgm'] / fga1, 4), round(me['fg3m'] / (me['fg3a'] or 1), 4), round(me['ftm'] / (me['fta'] or 1), 4),
                 me['oreb'], me['dreb'], me['pf'], me['pts_fb'], me['pts_paint'], pts - opp_pts,
                 round((me['fgm'] + 0.5 * me['fg3m']) / fga1, 4), round(me['tov'] / ((me['fga'] + 0.44 * me['fta'] - me['oreb'] + me['tov']) or 1), 4),
                 round(me['oreb'] / ((me['oreb'] + me['dreb']) or 1), 4), round(me['fta'] / fga1, 4),
                 round(off, 2), round(deff, 2), round(off - deff, 2), round(poss, 2), *q[:4], gdate,
                 'Playoffs' if stype == 3 else 'Regular Season'))
        # player logs
        for tp in s['boxscore'].get('players', []):
            abbr = ESPN_ABBR.get(tp['team']['abbreviation'], tp['team']['abbreviation'])
            tid = tmap[abbr]
            side = 'home' if tid == teams['home']['team_id'] else 'away'
            opp_id = teams['away' if side == 'home' else 'home']['team_id']
            won = to_int(c[side].get('score')) > to_int(c['away' if side == 'home' else 'home'].get('score'))
            for grp in tp['statistics']:
                labels = grp['labels']
                for a in grp['athletes']:
                    pid = pmap.get(norm(a['athlete']['displayName']))
                    if not pid or not a.get('stats') or a.get('didNotPlay'):
                        continue
                    row = dict(zip(labels, a['stats']))
                    mins = to_int(row.get('MIN'))
                    if mins <= 0:
                        continue
                    fgm, fga = pair(row.get('FG')); tpm, tpa = pair(row.get('3PT')); ftm, fta = pair(row.get('FT'))
                    cur.execute("""
                        INSERT INTO player_game_logs (game_id, player_id, team_id, opp_team_id, win, min, min_played,
                            pts, reb, ast, stl, blk, tov, fgm, fga, fg3m, fg3a, ftm, fta, fg_pct, fg3_pct, ft_pct,
                            oreb, dreb, pf, plus_minus, is_started, game_date)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (game_id, player_id) DO NOTHING""",
                        (gid, pid, tid, opp_id, won, mins, mins, to_int(row.get('PTS')), to_int(row.get('REB')),
                         to_int(row.get('AST')), to_int(row.get('STL')), to_int(row.get('BLK')), to_int(row.get('TO')),
                         fgm, fga, tpm, tpa, ftm, fta, round(fgm / (fga or 1), 4), round(tpm / (tpa or 1), 4),
                         round(ftm / (fta or 1), 4), to_int(row.get('OREB')), to_int(row.get('DREB')),
                         to_int(row.get('PF')), to_int(str(row.get('+/-', 0)).replace('+', '')),
                         bool(a.get('starter')), gdate))
        done += 1
    print(f"box scores ingested: {done}")


def fill_days_rest(cur):
    cur.execute("""
        WITH t AS (
          SELECT game_id, game_date, home_team_id AS team_id, true AS h FROM games
          UNION ALL SELECT game_id, game_date, away_team_id, false FROM games),
        r AS (SELECT game_id, team_id, h,
                LEAST(7, COALESCE(game_date - LAG(game_date) OVER (PARTITION BY team_id ORDER BY game_date, game_id), 7)) AS rest
              FROM t)
        UPDATE games g SET home_days_rest = rh.rest, away_days_rest = ra.rest
        FROM r rh, r ra
        WHERE rh.game_id = g.game_id AND rh.h AND ra.game_id = g.game_id AND NOT ra.h
          AND g.game_date >= '2026-06-01'""")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--back', type=int, default=3)
    ap.add_argument('--ahead', type=int, default=14)
    ap.add_argument('--from', dest='start')
    ap.add_argument('--to', dest='end')
    a = ap.parse_args()
    today = date.today()
    start = date.fromisoformat(a.start) if a.start else today - timedelta(days=a.back)
    end = date.fromisoformat(a.end) if a.end else today + timedelta(days=a.ahead)
    conn = connect()
    cur = conn.cursor()
    tm = team_map(cur)
    finals = sync_games(cur, tm, start, end)
    conn.commit()
    sync_box_scores(cur, finals, tm)
    fill_days_rest(cur)
    conn.commit()
    print("done")
