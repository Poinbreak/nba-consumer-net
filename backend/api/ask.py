"""
StatMuse-style natural-language stat questions, answered from our own database. Rule-based on purpose:
predictable, fast, and every answer is a SQL query we can show. Handles
  * league leaders        "most assists this season", "3-point leaders 2024-25", "highest ts% last season"
  * player lines          "Luka Doncic stats", "SGA last 10 games", "Jokic vs Lakers", "Wemby blocks career"
  * team records          "Thunder record", "Celtics record last season"
"""
import re
import unicodedata

from .db import REGULAR, SEASON_SQL, current_season, one, query, season_label

STATS = {  # key: (label, per-game expr, total expr, is_pct)
    'pts': ('Points', 'AVG(l.pts)', 'SUM(l.pts)', False),
    'reb': ('Rebounds', 'AVG(l.reb)', 'SUM(l.reb)', False),
    'ast': ('Assists', 'AVG(l.ast)', 'SUM(l.ast)', False),
    'stl': ('Steals', 'AVG(l.stl)', 'SUM(l.stl)', False),
    'blk': ('Blocks', 'AVG(l.blk)', 'SUM(l.blk)', False),
    'tov': ('Turnovers', 'AVG(l.tov)', 'SUM(l.tov)', False),
    'fg3m': ('3-Pointers Made', 'AVG(l.fg3m)', 'SUM(l.fg3m)', False),
    'min': ('Minutes', 'AVG(l.min_played)', 'SUM(l.min_played)', False),
    'fg_pct': ('FG%', '100.0*SUM(l.fgm)/NULLIF(SUM(l.fga),0)', None, True),
    'fg3_pct': ('3P%', '100.0*SUM(l.fg3m)/NULLIF(SUM(l.fg3a),0)', None, True),
    'ft_pct': ('FT%', '100.0*SUM(l.ftm)/NULLIF(SUM(l.fta),0)', None, True),
    'ts_pct': ('TS%', '100.0*SUM(l.pts)/NULLIF(2*(SUM(l.fga)+0.44*SUM(l.fta)),0)', None, True),
}
SYNONYMS = [  # (regex, stat key) - first match wins, so specific phrases come first
    (r'\b(3[- ]?point(ers?)?|threes?|3s|3pm)\b.*\b(made|makes)\b|\bmost (3[- ]?point(ers?)?|threes)\b|\bthree[- ]pointers? made\b', 'fg3m'),
    (r'\bts ?%|true shooting', 'ts_pct'),
    (r'\b(3p ?%|3[- ]?point (percentage|pct|%)|three point percentage)', 'fg3_pct'),
    (r'\b(ft ?%|free throw (percentage|pct|%))', 'ft_pct'),
    (r'\b(fg ?%|field goal (percentage|pct|%)|shooting percentage)', 'fg_pct'),
    (r'\b(3[- ]?point(ers?)?|threes?|3s)\b', 'fg3m'),
    (r'\b(points?|pts|scor\w+|ppg)\b', 'pts'),
    (r'\b(rebounds?|rebs?|boards?|rpg)\b', 'reb'),
    (r'\b(assists?|asts?|dimes|apg)\b', 'ast'),
    (r'\b(steals?|stl|spg)\b', 'stl'),
    (r'\b(blocks?|blk|bpg)\b', 'blk'),
    (r'\b(turnovers?|tov)\b', 'tov'),
    (r'\bminutes|\bmpg\b', 'min'),
]
ALIASES = {'sixers': 'philadelphia 76ers', 'wolves': 'minnesota timberwolves', 'cavs': 'cleveland cavaliers',
           'mavs': 'dallas mavericks', 'blazers': 'portland trail blazers', 'nugs': 'denver nuggets',
           'sga': 'shai gilgeous-alexander', 'wemby': 'victor wembanyama', 'jokic': 'nikola jokic',
           'luka': 'luka doncic', 'giannis': 'giannis antetokounmpo', 'steph': 'stephen curry',
           'lebron': 'lebron james', 'kd': 'kevin durant', 'ant': 'anthony edwards', 'melo': 'lamelo ball'}


def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r"[^a-z0-9%\- ]", ' ', s.replace('.', ''))).strip()


_cache = {}


def _players():
    if 'players' not in _cache:
        rows = query("""SELECT p.player_id, p.full_name, p.is_active, p.team_id,
                               (SELECT COUNT(*) FROM player_game_logs l WHERE l.player_id = p.player_id) AS n
                        FROM players p WHERE p.is_active OR EXISTS (SELECT 1 FROM player_game_logs l WHERE l.player_id = p.player_id)""")
        full, last = {}, {}
        for r in rows:
            key = norm(r['full_name'])
            if key not in full or (r['is_active'], r['n']) > (full[key]['is_active'], full[key]['n']):
                full[key] = r
            ln = key.split(' ')[-1]
            last.setdefault(ln, []).append(r)
        _cache['players'] = (full, last)
    return _cache['players']


def _teams():
    if 'teams' not in _cache:
        rows = query("""SELECT team_id, abbreviation, full_name, city FROM teams
                        WHERE team_id BETWEEN 1610612737 AND 1610612766""")
        names = {}
        for r in rows:
            nick = norm(r['full_name']).replace(norm(r['city'] or ''), '').strip() or norm(r['full_name'])
            for k in {nick, norm(r['full_name']), r['abbreviation'].lower()}:
                names[k] = r
            names[nick.split(' ')[-1]] = r
        _cache['teams'] = (rows, names)
    return _cache['teams']


def find_team(q):
    _, names = _teams()
    for k, v in ALIASES.items():
        if re.search(rf'\b{k}\b', q) and v in names:
            return names[v]
    for k in sorted(names, key=len, reverse=True):
        if len(k) > 3 and re.search(rf'\b{re.escape(k)}\b', q):
            return names[k]
    return None


def find_player(q):
    full, last = _players()
    for k, v in ALIASES.items():
        if re.search(rf'\b{k}\b', q) and v in full:
            return full[v], re.sub(rf'\b{k}\b', ' ', q)
    words = q.split()
    for size in (4, 3, 2):
        for i in range(len(words) - size + 1):
            key = ' '.join(words[i:i + size])
            if key in full:
                return full[key], ' '.join(words[:i] + words[i + size:])
    for i, w in enumerate(words):                      # unique last name among relevant players
        c = last.get(w, [])
        if len(w) > 3 and len(c) >= 1:
            best = max(c, key=lambda r: (r['is_active'], r['n']))
            if len(c) == 1 or best['is_active']:
                return best, ' '.join(words[:i] + words[i + 1:])
    return None, q


def find_stat(q):
    for rx, key in SYNONYMS:
        if re.search(rx, q):
            return key
    return None


def find_season(q):
    cs = current_season()
    if re.search(r'\bcareer|all[- ]time\b', q):
        return None, 'career'
    m = re.search(r'\b(20\d\d)[-/](\d\d)\b', q)
    if m:
        return int(m.group(1)) + 1, f"{m.group(1)}-{m.group(2)}"
    m = re.search(r'\b(?:in|during)\s+(20\d\d)\b', q)
    if m:
        return int(m.group(1)), season_label(int(m.group(1)))
    if re.search(r'\blast season|previous season\b', q):
        return cs - 1, season_label(cs - 1)
    return cs, season_label(cs)


def fmt(v, pct=False):
    if v is None:
        return '-'
    return f"{v:.1f}" if (pct or isinstance(v, float)) else str(v)


def leaders(q, stat, season, label):
    name, per_game, total, is_pct = STATS[stat]
    use_total = bool(total) and bool(re.search(r'\btotal|\bmost\b(?!.*per game)(?!.*(average|avg|ppg|per))', q)) \
        and not re.search(r'\bper game|\bppg|average|avg|\bpg\b', q)
    expr = total if use_total else per_game
    cs = season or current_season()
    max_g = one(f"SELECT MAX(n) m FROM (SELECT COUNT(*) n FROM team_game_stats WHERE {SEASON_SQL}=%s AND COALESCE(game_type,'Regular Season') IN {REGULAR} GROUP BY team_id) x", (cs,))['m'] or 82
    min_g = 1 if use_total else max(5, int(max_g * 0.5))
    season_filter = f"{SEASON_SQL} = %s" if season else "TRUE"
    attempts = {'fg_pct': 'fga', 'fg3_pct': 'fg3a', 'ft_pct': 'fta', 'ts_pct': 'fga'}.get(stat)   # qualify on the stat's own attempts
    per_game_min = {'fga': 5, 'fg3a': 2.5, 'fta': 2}.get(attempts)
    having = f"HAVING COUNT(*) >= {min_g}" + (f" AND SUM(l.{attempts}) >= {per_game_min}*COUNT(*)" if is_pct and attempts else "")
    rows = query(f"""
        SELECT p.player_id, p.full_name AS player, t.abbreviation AS team, s.g, ROUND(s.v::numeric, {0 if use_total else 1}) AS v, p.headshot_url
        FROM (SELECT l.player_id, COUNT(*) g, {expr} v, (ARRAY_AGG(l.team_id ORDER BY l.game_date DESC))[1] tid
              FROM player_game_logs l WHERE {season_filter} AND COALESCE(l.game_type,'Regular Season') IN {REGULAR}
              GROUP BY l.player_id {having}) s
        JOIN players p ON p.player_id = s.player_id LEFT JOIN teams t ON t.team_id = s.tid
        WHERE s.v IS NOT NULL ORDER BY s.v DESC LIMIT 10""", (cs,) if season else ())
    if not rows:
        return None
    top = rows[0]
    per = '' if is_pct else ('total ' if use_total else '')
    avg = '' if (is_pct or use_total) else ' per game'
    when = f"in {label}" if season else "for his career"
    answer = f"{top['player']} leads the NBA in {per}{name.lower()}{avg} {when} with {int(top['v']) if use_total else fmt(top['v'], True)}."
    title_kind = ('total' if use_total else 'per game') if not is_pct else ''
    return {'kind': 'leaders', 'answer': answer, 'title': f"{name} {title_kind} leaders · {label}".replace('  ', ' '),
            'columns': [{'key': 'rank', 'label': '#'}, {'key': 'player', 'label': 'Player'}, {'key': 'team', 'label': 'Team'},
                        {'key': 'g', 'label': 'GP'}, {'key': 'v', 'label': name, 'highlight': True}],
            'rows': [{**r, 'rank': i + 1, 'link': f"/player/{r['player_id']}"} for i, r in enumerate(rows)]}


def player_answer(q, player, rest, stat):
    pid = player['player_id']
    info = one("""SELECT p.player_id, p.full_name, p.position, p.headshot_url, p.jersey_number, t.abbreviation AS team, t.team_id
                  FROM players p LEFT JOIN teams t ON t.team_id = p.team_id WHERE p.player_id = %s""", (pid,))
    season, label = find_season(rest)
    n = None
    m = re.search(r'\blast (\d+)(?: games?)?\b', rest)
    if m:
        n = min(int(m.group(1)), 82)
    opp = find_team(rest) if re.search(r'\b(vs|against|versus|v)\b', rest) else None
    playoffs = bool(re.search(r'\bplayoffs?\b', rest))
    gtypes = "('Playoffs')" if playoffs else REGULAR
    where, params = ["l.player_id = %s", f"COALESCE(l.game_type,'Regular Season') IN {gtypes}"], [pid]
    if season and not n:
        where.append(f"{SEASON_SQL} = %s")
        params.append(season)
    if opp:
        where.append("l.opp_team_id = %s")
        params.append(opp['team_id'])
    log_sql = f"""SELECT l.game_date, o.abbreviation AS opp, l.is_started, l.win, ROUND(l.min_played) AS min, l.pts, l.reb, l.ast, l.stl, l.blk, l.tov,
                         l.fgm, l.fga, l.fg3m, l.fg3a, l.plus_minus
                  FROM player_game_logs l LEFT JOIN teams o ON o.team_id = l.opp_team_id
                  WHERE {' AND '.join(where)} ORDER BY l.game_date DESC"""
    games = query(log_sql + (f" LIMIT {n}" if n else ""), tuple(params))
    if not games:
        return {'kind': 'empty', 'answer': f"No games found for {info['full_name']} with those filters.", 'rows': [], 'columns': []}
    g = len(games)
    avg = lambda k: sum((x[k] or 0) for x in games) / g
    ctx = ('in the playoffs' if playoffs else '') or ('' if season is None and not n else '')
    scope = f"over his last {g} games" if n else (f"vs {opp['full_name']}" if opp else ('for his career' if season is None else f"in {label}"))
    if playoffs and not n:
        scope = f"in the playoffs {'for his career' if season is None else label}" if not opp else scope
    parts = {'pts': 'points', 'reb': 'rebounds', 'ast': 'assists', 'stl': 'steals', 'blk': 'blocks', 'tov': 'turnovers', 'fg3m': '3-pointers'}
    focus = [stat] if stat in parts else ['pts', 'reb', 'ast']
    bits = [f"{avg(k):.1f} {parts[k]}" for k in focus]
    line = bits[0] if len(bits) == 1 else ', '.join(bits[:-1]) + f" and {bits[-1]}"
    answer = f"{info['full_name']} {'averaged' if (n or opp or season is None or (season and season != current_season())) else 'is averaging'} {line} {scope}{'' if n else f' ({g} games)'}."
    shown = games[:15]
    cols = ['game_date', 'opp', 'min', 'pts', 'reb', 'ast', 'stl', 'blk', 'tov']
    labels = {'game_date': 'Date', 'opp': 'Opp', 'min': 'MIN', 'pts': 'PTS', 'reb': 'REB', 'ast': 'AST', 'stl': 'STL', 'blk': 'BLK', 'tov': 'TOV'}
    summary = {'game_date': 'AVG', 'opp': '', **{k: round(avg(k), 1) for k in cols[2:]}}
    return {'kind': 'player', 'answer': answer, 'player': info, 'title': f"{info['full_name']} · {scope}",
            'columns': [{'key': k, 'label': labels[k], 'highlight': k in focus} for k in cols],
            'rows': [{**{k: (str(x[k]) if k == 'game_date' else x[k]) for k in cols}} for x in shown],
            'summary': summary, 'link': f"/player/{pid}"}


def team_answer(q, team):
    season, label = find_season(q)
    cs = season or current_season()
    r = one(f"""SELECT COUNT(*) FILTER (WHERE win) AS w, COUNT(*) FILTER (WHERE NOT win) AS l,
                       ROUND(AVG(pts),1) AS pts, ROUND(AVG(opp_pts),1) AS opp
                FROM team_game_stats WHERE team_id=%s AND {SEASON_SQL}=%s AND COALESCE(game_type,'Regular Season') IN {REGULAR}""",
            (team['team_id'], cs))
    if not r or not (r['w'] or r['l']):
        return None
    return {'kind': 'team', 'answer': f"The {team['full_name']} went {r['w']}-{r['l']} in {season_label(cs)}, scoring {r['pts']} and allowing {r['opp']} per game.",
            'team': team, 'columns': [{'key': 'w', 'label': 'W'}, {'key': 'l', 'label': 'L'}, {'key': 'pts', 'label': 'PTS'}, {'key': 'opp', 'label': 'OPP'}],
            'rows': [r], 'link': f"/team/{team['team_id']}", 'title': f"{team['full_name']} · {season_label(cs)}"}


def ask(question: str):
    q = norm(question)
    if not q:
        return {'kind': 'empty', 'answer': 'Ask me anything about the NBA.', 'rows': [], 'columns': []}
    stat = find_stat(q)
    player, rest = find_player(q)
    if player:
        return player_answer(q, player, rest, stat)
    if re.search(r'\b(most|leads?|leaders?|highest|best|top|who has|who leads|who averages)\b', q) and stat:
        season, label = find_season(q)
        res = leaders(q, stat, season, label)
        if res:
            return res
    team = find_team(q)
    if team and re.search(r'\brecord|wins|losses|how (many|did)\b', q):
        res = team_answer(q, team)
        if res:
            return res
    if team:
        return {'kind': 'redirect', 'answer': f"Opening the {team['full_name']}.", 'link': f"/team/{team['team_id']}", 'rows': [], 'columns': []}
    return {'kind': 'empty', 'rows': [], 'columns': [],
            'answer': "I couldn't parse that. Try “Luka Doncic last 10 games”, “most assists this season”, or “Thunder record”."}
