"""v2 REST API: direct-SQL, one round trip per resource. Mounted at /api/v2/."""
import os
import time
from datetime import date, timedelta

import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .ask import ask as run_ask
from .db import REGULAR, SEASON_SQL, current_season, one, parallel, query, season_label, ttl_cache

# Team accent colours (primary brand colour); abbreviations follow our teams table.
TEAM_COLORS = {
    'ATL': '#E03A3E', 'BOS': '#007A33', 'BKN': '#8A8D8F', 'CHA': '#1D8CAB', 'CHI': '#CE1141', 'CLE': '#B8264F',
    'DAL': '#0053BC', 'DEN': '#FEC524', 'DET': '#C8102E', 'GSW': '#FFC72C', 'HOU': '#CE1141', 'IND': '#FDBB30',
    'LAC': '#C8102E', 'LAL': '#FDB927', 'MEM': '#5D76A9', 'MIA': '#98002E', 'MIL': '#00A04E', 'MIN': '#236192',
    'NOP': '#85714D', 'NYK': '#F58426', 'OKC': '#007AC1', 'ORL': '#0077C0', 'PHI': '#006BB6', 'PHX': '#E56020',
    'POR': '#E03A3E', 'SAC': '#7B4FB7', 'SAS': '#C4CED4', 'TOR': '#CE1141', 'UTA': '#F9A01B', 'WAS': '#E31837',
}


def _bg(fn, *a):
    """Start a query now, collect later with .result(): lets an endpoint's independent queries overlap (DB is ~300 ms away)."""
    from .db import _executor
    return _executor.submit(fn, *a)


def _team_json_sql(alias, prefix):
    return f"{alias}.team_id AS {prefix}_id, {alias}.abbreviation AS {prefix}_abbr, {alias}.full_name AS {prefix}_name"


def _decorate(rows, *prefixes):
    for r in rows:
        for p in prefixes:
            r[f'{p}_color'] = TEAM_COLORS.get(r.get(f'{p}_abbr'), '#8b8b95')
    return rows


def _iso(rows, *keys):
    for r in rows:
        for k in keys:
            if r.get(k) is not None:
                r[k] = str(r[k])
    return rows


# ── Scoreboard ───────────────────────────────────────────────────────────────
@api_view(['GET'])
@ttl_cache(20)
def scoreboard(request):
    day = request.query_params.get('date')
    if not day:
        row = one("""SELECT COALESCE(
                       (SELECT MIN(game_date) FROM games WHERE game_date >= CURRENT_DATE - 1 AND status IN ('Live','Scheduled')),
                       (SELECT MAX(game_date) FROM games)) AS d""")
        day = str(row['d'])
    nav_f = _bg(one, """SELECT (SELECT MAX(game_date) FROM games WHERE game_date < %s) AS prev,
                        (SELECT MIN(game_date) FROM games WHERE game_date > %s) AS next""", (day, day))
    games = query(f"""
        SELECT g.game_id, g.game_date, g.status, g.home_score, g.away_score, g.quarter, g.time_remaining,
               {_team_json_sql('h', 'home')}, {_team_json_sql('a', 'away')},
               p.home_win_prob, p.key_driver, p.feature_snapshot->'predicted_score' AS predicted_score
        FROM games g JOIN teams h ON h.team_id = g.home_team_id JOIN teams a ON a.team_id = g.away_team_id
        LEFT JOIN game_predictions p ON p.game_id = g.game_id AND p.model_type = 'static'
        WHERE g.game_date = %s ORDER BY g.status = 'Final', g.game_id""", (day,))
    nav = nav_f.result()
    return Response({'date': day, 'prev': str(nav['prev']) if nav['prev'] else None,
                     'next': str(nav['next']) if nav['next'] else None,
                     'games': _iso(_decorate(games, 'home', 'away'), 'game_date')})


# ── Predictions / awards / odds ─────────────────────────────────────────────
@api_view(['GET'])
@ttl_cache(120)
def upcoming_predictions(request):
    limit = min(int(request.query_params.get('limit', 40)), 200)
    rows = query(f"""
        SELECT g.game_id, g.game_date, {_team_json_sql('h', 'home')}, {_team_json_sql('a', 'away')},
               p.home_win_prob, p.key_driver, p.feature_snapshot->'predicted_score' AS predicted_score,
               p.feature_snapshot->'drivers' AS drivers
        FROM games g JOIN game_predictions p ON p.game_id = g.game_id
        JOIN teams h ON h.team_id = g.home_team_id JOIN teams a ON a.team_id = g.away_team_id
        WHERE g.status = 'Scheduled' AND g.game_date >= CURRENT_DATE - 1
        ORDER BY g.game_date, g.game_id LIMIT %s""", (limit,))
    return Response({'games': _iso(_decorate(rows, 'home', 'away'), 'game_date')})


@api_view(['GET'])
@ttl_cache(300)
def awards(request):
    seasons_f = _bg(query, "SELECT DISTINCT season_label FROM award_predictions ORDER BY 1 DESC")
    label = request.query_params.get('season')
    if not label:
        label = one("SELECT season_label FROM award_predictions ORDER BY season_label DESC LIMIT 1")['season_label']
    rows = query("""
        SELECT ap.award, ap.predicted_rank AS rank, ap.award_share_pct AS share, ap.stats_snapshot AS stats,
               p.player_id, p.full_name AS player, p.headshot_url, t.abbreviation AS team
        FROM award_predictions ap JOIN players p ON p.player_id = ap.player_id
        LEFT JOIN teams t ON t.team_id = ap.team_id
        WHERE ap.season_label = %s AND ap.predicted_rank <= 10 ORDER BY ap.award, ap.predicted_rank""", (label,))
    out = {}
    for r in rows:
        r['team_color'] = TEAM_COLORS.get(r['team'], '#8b8b95')
        out.setdefault(r['award'], []).append(r)
    seasons = [r['season_label'] for r in seasons_f.result()]
    return Response({'season': label, 'seasons': seasons, 'awards': out})


@api_view(['GET'])
@ttl_cache(300)
def title_odds(request):
    rows = query("""
        SELECT sp.*, t.abbreviation AS abbr, t.full_name AS name, t.conference
        FROM season_projections sp JOIN teams t ON t.team_id = sp.team_id
        WHERE sp.season_label = (SELECT MAX(season_label) FROM season_projections)
        ORDER BY sp.title_prob DESC""")
    for r in rows:
        r['color'] = TEAM_COLORS.get(r['abbr'], '#8b8b95')
        r['updated_at'] = str(r['updated_at'])
    return Response({'season': rows[0]['season_label'] if rows else None, 'teams': rows})


_odds_cache = {'t': 0, 'data': None}


@api_view(['GET'])
def odds(request):
    """Live moneylines from The Odds API (cached 10 min to protect the free quota) joined to model probabilities."""
    key = os.environ.get('ODDS_API_KEY')
    if not key:
        return Response({'error': 'ODDS_API_KEY not configured', 'games': []}, status=200)
    if time.time() - _odds_cache['t'] > 600 or _odds_cache['data'] is None:
        try:
            r = requests.get('https://api.the-odds-api.com/v4/sports/basketball_nba/odds/',
                             params={'apiKey': key, 'regions': 'us', 'markets': 'h2h,spreads,totals', 'oddsFormat': 'american'}, timeout=15)
            r.raise_for_status()
            _odds_cache.update(t=time.time(), data=r.json(), remaining=r.headers.get('x-requests-remaining'))
        except requests.RequestException as e:
            if _odds_cache['data'] is None:
                return Response({'error': f'odds provider unavailable: {e}', 'games': []})
    teams = {t['full_name'].lower().replace('los angeles clippers', 'la clippers'): t
             for t in query("SELECT team_id, abbreviation, full_name FROM teams WHERE team_id BETWEEN 1610612737 AND 1610612766")}
    teams['la clippers'] = teams.get('la clippers') or next((t for t in teams.values() if t['abbreviation'] == 'LAC'), None)

    def implied(price):
        return 100 / (price + 100) if price > 0 else -price / (-price + 100)

    model_probs = {}
    for r in query("""SELECT g.home_team_id, g.away_team_id, p.home_win_prob FROM games g
                     JOIN game_predictions p ON p.game_id = g.game_id
                     WHERE g.status = 'Scheduled' AND g.game_date BETWEEN CURRENT_DATE - 1 AND CURRENT_DATE + 7
                     ORDER BY g.game_date DESC"""):
        model_probs[(r['home_team_id'], r['away_team_id'])] = r['home_win_prob']   # earliest game wins (ordered DESC)
    out = []
    for g in _odds_cache['data']:
        h, a = teams.get(g['home_team'].lower()), teams.get(g['away_team'].lower())
        books, best = [], {'home': None, 'away': None}
        spread = total = None
        for b in g.get('bookmakers', []):
            for m in b['markets']:
                if m['key'] == 'h2h':
                    prices = {o['name']: o['price'] for o in m['outcomes']}
                    ph, pa = prices.get(g['home_team']), prices.get(g['away_team'])
                    if ph is None or pa is None:
                        continue
                    books.append({'book': b['title'], 'home': ph, 'away': pa})
                    best['home'] = ph if best['home'] is None or ph > best['home'] else best['home']
                    best['away'] = pa if best['away'] is None or pa > best['away'] else best['away']
                elif m['key'] == 'spreads' and spread is None:
                    for o in m['outcomes']:
                        if o['name'] == g['home_team']:
                            spread = o.get('point')
                elif m['key'] == 'totals' and total is None:
                    total = m['outcomes'][0].get('point')
        if not books:
            continue
        # market probability: average de-vigged implied prob across books
        mk = sum(implied(b['home']) / (implied(b['home']) + implied(b['away'])) for b in books) / len(books)
        model = model_probs.get((h['team_id'], a['team_id'])) if h and a else None
        out.append({'id': g['id'], 'commence': g['commence_time'], 'home': g['home_team'], 'away': g['away_team'],
                    'home_abbr': h['abbreviation'] if h else None, 'away_abbr': a['abbreviation'] if a else None,
                    'home_color': TEAM_COLORS.get(h['abbreviation']) if h else '#8b8b95',
                    'away_color': TEAM_COLORS.get(a['abbreviation']) if a else '#8b8b95',
                    'best': best, 'books': books, 'spread': spread, 'total': total,
                    'market_home_prob': round(mk, 4), 'model_home_prob': model,
                    'edge_home': round(model - mk, 4) if model is not None else None})
    return Response({'games': out, 'requests_remaining': _odds_cache.get('remaining')})


# ── Players ──────────────────────────────────────────────────────────────────
@api_view(['GET'])
@ttl_cache(300)
def player_search(request):
    q = request.query_params.get('q', '').strip()
    if len(q) < 2:
        return Response({'results': []})
    rows = query("""
        SELECT p.player_id, p.full_name, p.position, p.is_active, p.headshot_url, t.abbreviation AS team
        FROM players p LEFT JOIN teams t ON t.team_id = p.team_id
        WHERE p.full_name ILIKE %s AND (p.is_active OR EXISTS (SELECT 1 FROM player_game_logs l WHERE l.player_id = p.player_id))
        ORDER BY p.is_active DESC, (p.full_name ILIKE %s) DESC, p.full_name LIMIT 8""", (f'%{q}%', f'{q}%'))
    return Response({'results': rows})


@api_view(['GET'])
@ttl_cache(120)
def player_detail(request, player_id):
    p_f = _bg(one, """SELECT p.player_id, p.full_name, p.position, p.age, p.jersey_number, p.height_in, p.weight_lb, p.headshot_url,
                      p.college, p.experience, p.is_active, t.team_id, t.abbreviation AS team, t.full_name AS team_name
               FROM players p LEFT JOIN teams t ON t.team_id = p.team_id WHERE p.player_id = %s""", (player_id,))
    seasons_f = _bg(query, f"""
        SELECT {SEASON_SQL} AS season, (ARRAY_AGG(l.team_id ORDER BY l.game_date DESC))[1] AS tid, COUNT(*) AS g,
               SUM(l.is_started::int) AS gs, ROUND(AVG(l.min_played),1) AS mpg, ROUND(AVG(l.pts),1) AS pts,
               ROUND(AVG(l.reb),1) AS reb, ROUND(AVG(l.ast),1) AS ast, ROUND(AVG(l.stl),1) AS stl, ROUND(AVG(l.blk),1) AS blk,
               ROUND(AVG(l.tov),1) AS tov,
               ROUND(100.0*SUM(l.fgm)/NULLIF(SUM(l.fga),0),1) AS fg_pct, ROUND(100.0*SUM(l.fg3m)/NULLIF(SUM(l.fg3a),0),1) AS fg3_pct,
               ROUND(100.0*SUM(l.ftm)/NULLIF(SUM(l.fta),0),1) AS ft_pct,
               ROUND(100.0*SUM(l.pts)/NULLIF(2*(SUM(l.fga)+0.44*SUM(l.fta)),0),1) AS ts_pct
        FROM player_game_logs l WHERE l.player_id = %s AND COALESCE(l.game_type,'Regular Season') IN {REGULAR}
        GROUP BY 1 ORDER BY 1 DESC""", (player_id,))
    abbr_f = _bg(query, "SELECT team_id, abbreviation FROM teams")
    career_f = _bg(one, f"""
        SELECT COUNT(*) AS g, ROUND(AVG(pts),1) AS pts, ROUND(AVG(reb),1) AS reb, ROUND(AVG(ast),1) AS ast,
               ROUND(AVG(stl),1) AS stl, ROUND(AVG(blk),1) AS blk, ROUND(AVG(min_played),1) AS mpg,
               ROUND(100.0*SUM(fgm)/NULLIF(SUM(fga),0),1) AS fg_pct, ROUND(100.0*SUM(fg3m)/NULLIF(SUM(fg3a),0),1) AS fg3_pct,
               ROUND(100.0*SUM(pts)/NULLIF(2*(SUM(fga)+0.44*SUM(fta)),0),1) AS ts_pct
        FROM player_game_logs WHERE player_id = %s AND COALESCE(game_type,'Regular Season') IN {REGULAR}""", (player_id,))
    log_f = _bg(query, """
        SELECT l.game_date, o.abbreviation AS opp, l.win, ROUND(l.min_played) AS min, l.pts, l.reb, l.ast, l.stl, l.blk, l.tov,
               l.fgm, l.fga, l.fg3m, l.fg3a, l.plus_minus, l.game_type
        FROM player_game_logs l LEFT JOIN teams o ON o.team_id = l.opp_team_id
        WHERE l.player_id = %s ORDER BY l.game_date DESC LIMIT 20""", (player_id,))
    contract_f = _bg(one, "SELECT season_label, salary, years_remaining, option_type FROM contracts WHERE player_id = %s ORDER BY season_label DESC LIMIT 1", (player_id,))
    injury_f = _bg(one, "SELECT status, reason FROM injuries WHERE player_id = %s", (player_id,))
    award_f = _bg(query, "SELECT award, predicted_rank AS rank, award_share_pct AS share, season_label FROM award_predictions WHERE player_id = %s AND predicted_rank <= 5 ORDER BY season_label DESC", (player_id,))
    p, seasons, career, log, contract, injury, award_rows = (x.result() for x in (p_f, seasons_f, career_f, log_f, contract_f, injury_f, award_f))
    abbr = {t['team_id']: t['abbreviation'] for t in abbr_f.result()}
    if not p:
        return Response({'error': 'not found'}, status=404)
    p['team_color'] = TEAM_COLORS.get(p['team'], '#8b8b95')
    for s in seasons:
        s['label'] = season_label(int(s['season']))
        s['team'] = abbr.get(s.pop('tid'))
    return Response({'player': p, 'seasons': seasons, 'career': career, 'game_log': _iso(log, 'game_date'),
                     'contract': contract, 'injury': injury, 'awards': award_rows})


@api_view(['GET'])
@ttl_cache(300)
def leaders(request):
    from .ask import STATS, leaders as run_leaders
    stat = request.query_params.get('stat', 'pts')
    stat = stat if stat in STATS else 'pts'
    cs = current_season()
    res = run_leaders('', stat, cs, season_label(cs))
    return Response(res or {'rows': []})


# ── Teams ────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@ttl_cache(120)
def teams_list(request):
    cs = current_season()
    rows = query(f"""
        SELECT t.team_id, t.abbreviation AS abbr, t.full_name AS name, t.conference, t.division,
               COUNT(s.*) FILTER (WHERE s.win) AS w, COUNT(s.*) FILTER (WHERE NOT s.win) AS l,
               ROUND(AVG(s.pts),1) AS pts, ROUND(AVG(s.opp_pts),1) AS opp_pts, ROUND(AVG(s.net_rating),1) AS net_rating,
               sp.exp_wins, sp.title_prob, sp.playoff_prob
        FROM teams t LEFT JOIN team_game_stats s ON s.team_id = t.team_id AND {SEASON_SQL.replace('game_date', 's.game_date')} = %s
               AND COALESCE(s.game_type,'Regular Season') IN {REGULAR}
        LEFT JOIN season_projections sp ON sp.team_id = t.team_id AND sp.season_label = (SELECT MAX(season_label) FROM season_projections)
        WHERE t.team_id BETWEEN 1610612737 AND 1610612766
        GROUP BY t.team_id, sp.exp_wins, sp.title_prob, sp.playoff_prob ORDER BY t.conference, w DESC""", (cs,))
    for r in rows:
        r['color'] = TEAM_COLORS.get(r['abbr'], '#8b8b95')
    return Response({'season': season_label(cs), 'teams': rows})


@api_view(['GET'])
@ttl_cache(120)
def team_detail(request, team_id):
    t_f = _bg(one, "SELECT team_id, abbreviation AS abbr, full_name AS name, conference, division FROM teams WHERE team_id = %s", (team_id,))
    cs = current_season()
    record_f = _bg(one, f"""SELECT COUNT(*) FILTER (WHERE win) AS w, COUNT(*) FILTER (WHERE NOT win) AS l, ROUND(AVG(pts),1) AS pts,
                            ROUND(AVG(opp_pts),1) AS opp_pts, ROUND(AVG(off_rating),1) AS off_rating, ROUND(AVG(def_rating),1) AS def_rating,
                            ROUND(AVG(net_rating),1) AS net_rating, ROUND(AVG(pace),1) AS pace
                     FROM team_game_stats WHERE team_id = %s AND {SEASON_SQL} = %s AND COALESCE(game_type,'Regular Season') IN {REGULAR}""", (team_id, cs))
    history_f = _bg(query, f"""SELECT {SEASON_SQL} AS season, COUNT(*) FILTER (WHERE win) AS w, COUNT(*) FILTER (WHERE NOT win) AS l,
                               ROUND(AVG(net_rating),1) AS net_rating
                        FROM team_game_stats WHERE team_id = %s AND COALESCE(game_type,'Regular Season') IN {REGULAR}
                        GROUP BY 1 ORDER BY 1 DESC""", (team_id,))
    roster_f = _bg(query, f"""
        SELECT p.player_id, p.full_name, p.position, p.age, p.jersey_number, p.headshot_url, c.salary, i.status AS injury,
               a.g, a.mpg, a.pts, a.reb, a.ast
        FROM players p
        LEFT JOIN contracts c ON c.player_id = p.player_id AND c.season_label = (SELECT MAX(season_label) FROM contracts)
        LEFT JOIN injuries i ON i.player_id = p.player_id
        LEFT JOIN LATERAL (SELECT COUNT(*) g, ROUND(AVG(min_played),1) mpg, ROUND(AVG(pts),1) pts, ROUND(AVG(reb),1) reb, ROUND(AVG(ast),1) ast
                           FROM player_game_logs l WHERE l.player_id = p.player_id AND l.game_date >= %s AND l.game_date < %s
                           AND COALESCE(l.game_type,'Regular Season') IN {REGULAR}) a ON TRUE
        WHERE p.team_id = %s AND p.is_active ORDER BY a.mpg DESC NULLS LAST, c.salary DESC NULLS LAST""", (f'{cs - 1}-08-01', f'{cs}-08-01', team_id))
    schedule_f = _bg(query, f"""
        SELECT g.game_id, g.game_date, g.status, g.home_score, g.away_score, (g.home_team_id = %s) AS is_home,
               o.abbreviation AS opp, o.full_name AS opp_name, p.home_win_prob
        FROM games g JOIN teams o ON o.team_id = CASE WHEN g.home_team_id = %s THEN g.away_team_id ELSE g.home_team_id END
        LEFT JOIN game_predictions p ON p.game_id = g.game_id
        WHERE (g.home_team_id = %s OR g.away_team_id = %s) AND g.game_date >= CURRENT_DATE - 14
        ORDER BY g.game_date LIMIT 20""", (team_id, team_id, team_id, team_id))
    projection_f = _bg(one, "SELECT * FROM season_projections WHERE team_id = %s ORDER BY season_label DESC LIMIT 1", (team_id,))
    t, record, history, roster, schedule, projection = (x.result() for x in (t_f, record_f, history_f, roster_f, schedule_f, projection_f))
    if not t:
        return Response({'error': 'not found'}, status=404)
    t['color'] = TEAM_COLORS.get(t['abbr'], '#8b8b95')
    for h in history:
        h['label'] = season_label(int(h['season']))
    for s in schedule:
        s['win_prob'] = None if s['home_win_prob'] is None else (s['home_win_prob'] if s['is_home'] else round(1 - s['home_win_prob'], 4))
        s.pop('home_win_prob')
    if projection:
        projection['updated_at'] = str(projection['updated_at'])
    return Response({'team': t, 'season': season_label(cs), 'record': record, 'history': history, 'roster': roster,
                     'schedule': _iso(schedule, 'game_date'), 'projection': projection})


# ── Ask ──────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@ttl_cache(120)
def ask_view(request):
    try:
        return Response(run_ask(request.query_params.get('q', '')))
    except Exception as e:  # keep the search box usable even if one parser branch fails
        return Response({'kind': 'empty', 'answer': f'Something went wrong answering that ({type(e).__name__}).', 'rows': [], 'columns': []})
