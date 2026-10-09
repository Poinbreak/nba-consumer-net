"""
Rebuild current rosters, contracts and injuries from ESPN.

Resets players.team_id/is_active, then sets them from each team's live roster, so offseason
trades / signings are reflected. Players not in the Kaggle `players` table (rookies, two-ways)
are inserted with player_id = 1_000_000_000 + espn_id.

    python scripts/sync_rosters.py
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../ml'))
from features import connect  # noqa: E402
from sync_scores import ESPN_ABBR, get, norm, team_map  # noqa: E402

CORE = 'https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/athletes/%s/contracts/%s'


def fetch_contract(args):
    espn_id, year = args
    for y in (year, year - 1):
        try:
            r = requests.get(CORE % (espn_id, y), timeout=15)
            if r.status_code == 200:
                j = r.json()
                return espn_id, y, j
        except requests.RequestException:
            pass
    return espn_id, None, None


def main():
    conn = connect()
    cur = conn.cursor()
    tmap = team_map(cur)
    espn_teams = get('teams')['sports'][0]['leagues'][0]['teams']

    cur.execute("""SELECT p.player_id, p.full_name FROM players p
                   ORDER BY EXISTS (SELECT 1 FROM player_game_logs l WHERE l.player_id=p.player_id AND l.game_date > '2024-10-01')""")
    by_name = {norm(n): i for i, n in cur.fetchall()}   # players with recent logs win name collisions

    cur.execute("UPDATE players SET team_id = NULL, is_active = FALSE")
    cur.execute("DELETE FROM injuries")
    roster, season_year = [], None
    for t in espn_teams:
        abbr = ESPN_ABBR.get(t['team']['abbreviation'], t['team']['abbreviation'])
        tid = tmap.get(abbr)
        if tid is None:
            continue
        r = get(f"teams/{t['team']['id']}/roster")
        season_year = season_year or r.get('season', {}).get('year')
        for a in r['athletes']:
            eid = int(a['id'])
            pid = by_name.get(norm(a['fullName']))
            pos = (a.get('position') or {}).get('abbreviation')
            vals = dict(team_id=tid, position=pos, age=a.get('age'), jersey_number=a.get('jersey'),
                        espn_id=eid, height_in=a.get('height'), weight_lb=a.get('weight'),
                        headshot_url=f'https://a.espncdn.com/i/headshots/nba/players/full/{eid}.png',
                        experience=(a.get('experience') or {}).get('years'),
                        college=(a.get('college') or {}).get('name'))
            if pid is None:
                pid = 1_000_000_000 + eid
                cur.execute("INSERT INTO players (player_id, full_name) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                            (pid, a['fullName']))
            cur.execute("""UPDATE players SET team_id=%(team_id)s, position=%(position)s, age=%(age)s,
                           jersey_number=%(jersey_number)s, is_active=TRUE, espn_id=%(espn_id)s,
                           height_in=%(height_in)s, weight_lb=%(weight_lb)s, headshot_url=%(headshot_url)s,
                           experience=%(experience)s, college=%(college)s WHERE player_id=%(pid)s""",
                        {**vals, 'pid': pid})
            for inj in a.get('injuries') or []:
                cur.execute("""INSERT INTO injuries (player_id, status, reason, espn_status, updated_at)
                               VALUES (%s,%s,%s,%s, now()) ON CONFLICT (player_id) DO NOTHING""",
                            (pid, (inj.get('status') or '')[:20], inj.get('shortComment') or inj.get('longComment'),
                             inj.get('status')))
            roster.append((pid, eid, tid))
    conn.commit()
    print(f"rosters: {len(roster)} players across {len(espn_teams)} teams")

    year = season_year or 2026
    label = f"{year - 1}-{str(year)[2:]}"
    with ThreadPoolExecutor(12) as ex:
        results = list(ex.map(fetch_contract, [(e, year) for _, e, _ in roster]))
    by_espn = {e: (p, t) for p, e, t in roster}
    n = 0
    for eid, y, j in results:
        if not j:
            continue
        pid, tid = by_espn[eid]
        sal = j.get('salary') or 0
        cur.execute("""INSERT INTO contracts (player_id, team_id, season_label, salary, years_remaining,
                         is_expiring, option_type, trade_restriction)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (player_id, season_label) DO UPDATE SET team_id=EXCLUDED.team_id,
                         salary=EXCLUDED.salary, years_remaining=EXCLUDED.years_remaining,
                         is_expiring=EXCLUDED.is_expiring, option_type=EXCLUDED.option_type,
                         trade_restriction=EXCLUDED.trade_restriction""",
                    (pid, tid, label, sal, j.get('yearsRemaining'), (j.get('yearsRemaining') or 0) <= 1,
                     j.get('optionType') or 0, bool(j.get('tradeRestriction'))))
        n += 1
    conn.commit()
    print(f"contracts: {n} for {label}")


if __name__ == '__main__':
    main()
