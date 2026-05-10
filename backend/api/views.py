from rest_framework.decorators import api_view
from rest_framework.response import Response
from supabase import create_client, Client
import os, math, numpy as np, joblib, requests as req_lib
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()
supabase: Client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# ── Static team metadata ─────────────────────────────────────────────────────
TEAM_META = {
    1610612737: {'abbrev': 'ATL', 'name': 'Atlanta Hawks',           'accent': '#E03A3E'},
    1610612738: {'abbrev': 'BOS', 'name': 'Boston Celtics',          'accent': '#007A33'},
    1610612739: {'abbrev': 'CLE', 'name': 'Cleveland Cavaliers',     'accent': '#860038'},
    1610612740: {'abbrev': 'NOP', 'name': 'New Orleans Pelicans',    'accent': '#0C2340'},
    1610612741: {'abbrev': 'CHI', 'name': 'Chicago Bulls',           'accent': '#CE1141'},
    1610612742: {'abbrev': 'DAL', 'name': 'Dallas Mavericks',        'accent': '#00538C'},
    1610612743: {'abbrev': 'DEN', 'name': 'Denver Nuggets',          'accent': '#0E2240'},
    1610612744: {'abbrev': 'GSW', 'name': 'Golden State Warriors',   'accent': '#1D428A'},
    1610612745: {'abbrev': 'HOU', 'name': 'Houston Rockets',         'accent': '#CE1141'},
    1610612746: {'abbrev': 'LAC', 'name': 'LA Clippers',             'accent': '#C8102E'},
    1610612747: {'abbrev': 'LAL', 'name': 'Los Angeles Lakers',      'accent': '#552583'},
    1610612748: {'abbrev': 'MIA', 'name': 'Miami Heat',              'accent': '#98002E'},
    1610612749: {'abbrev': 'MIL', 'name': 'Milwaukee Bucks',         'accent': '#00471B'},
    1610612750: {'abbrev': 'MIN', 'name': 'Minnesota Timberwolves',  'accent': '#0C2340'},
    1610612751: {'abbrev': 'BKN', 'name': 'Brooklyn Nets',           'accent': '#000000'},
    1610612752: {'abbrev': 'NYK', 'name': 'New York Knicks',         'accent': '#006BB6'},
    1610612753: {'abbrev': 'ORL', 'name': 'Orlando Magic',           'accent': '#0077C0'},
    1610612754: {'abbrev': 'IND', 'name': 'Indiana Pacers',          'accent': '#002D62'},
    1610612755: {'abbrev': 'PHI', 'name': 'Philadelphia 76ers',      'accent': '#006BB6'},
    1610612756: {'abbrev': 'PHX', 'name': 'Phoenix Suns',            'accent': '#1D1160'},
    1610612757: {'abbrev': 'POR', 'name': 'Portland Trail Blazers',  'accent': '#E03A3E'},
    1610612758: {'abbrev': 'SAC', 'name': 'Sacramento Kings',        'accent': '#5A2D81'},
    1610612759: {'abbrev': 'SAS', 'name': 'San Antonio Spurs',       'accent': '#C4CED4'},
    1610612760: {'abbrev': 'OKC', 'name': 'Oklahoma City Thunder',   'accent': '#007AC1'},
    1610612761: {'abbrev': 'TOR', 'name': 'Toronto Raptors',         'accent': '#CE1141'},
    1610612762: {'abbrev': 'UTA', 'name': 'Utah Jazz',               'accent': '#002B5C'},
    1610612763: {'abbrev': 'MEM', 'name': 'Memphis Grizzlies',       'accent': '#5D76A9'},
    1610612764: {'abbrev': 'WAS', 'name': 'Washington Wizards',      'accent': '#002B5C'},
    1610612765: {'abbrev': 'DET', 'name': 'Detroit Pistons',         'accent': '#C8102E'},
    1610612766: {'abbrev': 'CHA', 'name': 'Charlotte Hornets',       'accent': '#1D1160'},
}
# reverse lookup: full name → team_id
NAME_TO_ID = {v['name'].lower(): k for k, v in TEAM_META.items()}


def _enrich_game(row):
    ht = TEAM_META.get(row.get('home_team_id'), {})
    at = TEAM_META.get(row.get('away_team_id'), {})
    return {
        **row,
        'home_team_abbrev':  ht.get('abbrev', '???'),
        'home_team_name':    ht.get('name', ''),
        'home_team_accent':  ht.get('accent', '#6c63ff'),
        'away_team_abbrev':  at.get('abbrev', '???'),
        'away_team_name':    at.get('name', ''),
        'away_team_accent':  at.get('accent', '#ff6b6b'),
        'home_win_prob': 50,
        'away_win_prob': 50,
    }


# ── 1. Live Scoreboard ───────────────────────────────────────────────────────
@api_view(['GET'])
def live_scoreboard(request):
    try:
        today     = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        res = supabase.table('games') \
            .select('game_id, home_team_id, away_team_id, status, home_score, away_score, quarter, time_remaining, game_date') \
            .gte('game_date', yesterday).lte('game_date', today) \
            .order('game_date', desc=True).limit(15).execute()

        if not res.data:
            five = (date.today() - timedelta(days=5)).isoformat()
            res = supabase.table('games') \
                .select('game_id, home_team_id, away_team_id, status, home_score, away_score, quarter, time_remaining, game_date') \
                .gte('game_date', five).order('game_date', desc=True).limit(10).execute()

        return Response({'games': [_enrich_game(g) for g in res.data], 'date': today})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ── 2. Game Prediction ───────────────────────────────────────────────────────
@api_view(['GET'])
def game_prediction(request, game_id):
    try:
        game_res = supabase.table('games') \
            .select('game_id, home_team_id, away_team_id, home_days_rest, away_days_rest') \
            .eq('game_id', str(game_id)).single().execute()
        game = game_res.data

        def get_rolling(team_id):
            r = supabase.table('team_rolling_stats') \
                .select('efg_pct_roll, tov_pct_roll, oreb_pct_roll, ft_rate_roll, net_rating_roll, fga_avg_roll') \
                .eq('team_id', team_id).eq('stat_window', 10) \
                .order('as_of_date', desc=True).limit(1).execute()
            return r.data[0] if r.data else {}

        safe = lambda d, k: d.get(k) or 0
        h, a = get_rolling(game['home_team_id']), get_rolling(game['away_team_id'])

        features = {
            'home_days_rest':  game.get('home_days_rest') or 2,
            'away_days_rest':  game.get('away_days_rest') or 2,
            'is_b2b_home':     1 if (game.get('home_days_rest') or 2) == 1 else 0,
            'is_b2b_away':     1 if (game.get('away_days_rest') or 2) == 1 else 0,
            'efg_pct_diff':    safe(h,'efg_pct_roll') - safe(a,'efg_pct_roll'),
            'tov_pct_diff':    safe(h,'tov_pct_roll') - safe(a,'tov_pct_roll'),
            'oreb_pct_diff':   safe(h,'oreb_pct_roll') - safe(a,'oreb_pct_roll'),
            'ft_rate_diff':    safe(h,'ft_rate_roll') - safe(a,'ft_rate_roll'),
            'net_rating_diff': safe(h,'net_rating_roll') - safe(a,'net_rating_roll'),
            'fga_diff':        safe(h,'fga_avg_roll') - safe(a,'fga_avg_roll'),
            'has_top10_home': 0, 'has_top10_away': 0, 'has_top25_home': 0, 'has_top25_away': 0,
        }

        FEATURE_ORDER = ['home_days_rest','away_days_rest','is_b2b_home','is_b2b_away',
                         'efg_pct_diff','tov_pct_diff','oreb_pct_diff','ft_rate_diff',
                         'net_rating_diff','fga_diff','has_top10_home','has_top10_away',
                         'has_top25_home','has_top25_away']
        DESCRIPTIONS = {
            'home_days_rest':'Home rest days','away_days_rest':'Away rest days',
            'is_b2b_home':'Home back-to-back','is_b2b_away':'Away back-to-back',
            'efg_pct_diff':'eFG% edge','tov_pct_diff':'Turnover rate edge',
            'oreb_pct_diff':'Offensive rebound edge','ft_rate_diff':'Free throw rate edge',
            'net_rating_diff':'Net rating differential','fga_diff':'Shot volume edge',
            'has_top10_home':'Top-10 player home','has_top10_away':'Top-10 player away',
            'has_top25_home':'Top-25 player home','has_top25_away':'Top-25 player away',
        }
        shap_factors, home_prob = [], None
        model_path    = os.path.join(os.path.dirname(__file__), '../ml/xgb_team_model.pkl')
        explainer_path = os.path.join(os.path.dirname(__file__), '../ml/shap_explainer.pkl')

        if os.path.exists(model_path):
            model = joblib.load(model_path)
            X = np.array([[features[f] for f in FEATURE_ORDER]])
            home_prob = float(model.predict_proba(X)[0][1])
            if os.path.exists(explainer_path):
                exp = joblib.load(explainer_path)
                sv = exp.shap_values(X)[0]
                shap_factors = [
                    {'feature': f, 'impact': round(float(v), 4), 'description': DESCRIPTIONS.get(f, f)}
                    for f, v in sorted(zip(FEATURE_ORDER, sv), key=lambda x: abs(x[1]), reverse=True)[:6]
                ]

        if home_prob is None:
            nd = features['net_rating_diff']
            home_prob = float(1 / (1 + np.exp(-nd * 0.15 - 0.1)))
            shap_factors = [
                {'feature': 'net_rating_diff', 'impact': round(nd * 0.05, 3), 'description': 'Net rating differential'},
                {'feature': 'home_days_rest',  'impact': round((features['home_days_rest']-2)*0.01, 3), 'description': 'Home rest advantage'},
                {'feature': 'is_b2b_away',     'impact': round(features['is_b2b_away']*-0.04, 3), 'description': 'Away B2B penalty'},
            ]

        return Response({
            'game_id': game_id,
            'home_win_probability': round(home_prob, 4),
            'away_win_probability': round(1 - home_prob, 4),
            'predicted_score': {'home': int(110 + features['net_rating_diff']*0.4), 'away': int(110 - features['net_rating_diff']*0.4)},
            'shap_factors': shap_factors,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ── 3. Player Props ──────────────────────────────────────────────────────────
@api_view(['GET'])
def player_props(request, game_id):
    try:
        game_res = supabase.table('games').select('home_team_id, away_team_id') \
            .eq('game_id', str(game_id)).single().execute()
        game = game_res.data
        props = []
        for team_id in [game['home_team_id'], game['away_team_id']]:
            # Get rolling stats per player on this team from player_season_avgs view
            res = supabase.table('player_season_avgs') \
                .select('player_id, full_name, pts_avg, reb_avg, ast_avg, fg_pct_avg, games_played') \
                .eq('team_id', team_id).order('pts_avg', desc=True).limit(8).execute()
            for r in res.data:
                props.append({**r, 'team_id': team_id,
                               'team_abbrev': TEAM_META.get(team_id, {}).get('abbrev', '?')})
        return Response({'game_id': game_id, 'props': props or []})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ── 4. Odds (matched to our games) ──────────────────────────────────────────
@api_view(['GET'])
def todays_odds(request):
    try:
        ODDS_KEY = os.environ.get('ODDS_API_KEY')
        resp = req_lib.get(
            'https://api.the-odds-api.com/v4/sports/basketball_nba/odds/',
            params={'apiKey': ODDS_KEY, 'regions': 'us', 'markets': 'h2h,spreads,totals', 'oddsFormat': 'american'},
            timeout=10
        )
        resp.raise_for_status()
        raw = resp.json()

        # Enrich each game with our team_id mapping so the frontend can join by ID
        enriched = []
        for g in raw:
            home_id = NAME_TO_ID.get(g['home_team'].lower())
            away_id = NAME_TO_ID.get(g['away_team'].lower())
            enriched.append({**g, 'home_team_id': home_id, 'away_team_id': away_id})
        return Response(enriched)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ── 5. Team Season Stats ─────────────────────────────────────────────────────
@api_view(['GET'])
def team_stats(request, team_id):
    try:
        meta = TEAM_META.get(team_id, {})
        # Season averages from view
        avgs_res = supabase.table('team_season_avgs').select('*').eq('team_id', team_id).execute()
        avgs = avgs_res.data[0] if avgs_res.data else {}

        # Last 10 games
        games_res = supabase.table('team_game_stats') \
            .select('game_id, game_date, win, pts, opp_pts, ast, reb, fg_pct, fg3_pct, plus_minus, opp_team_id, is_home') \
            .eq('team_id', team_id).order('game_date', desc=True).limit(10).execute()
        logs = [{
            **g,
            'opp_abbrev': TEAM_META.get(g.get('opp_team_id'), {}).get('abbrev', '???'),
        } for g in games_res.data]

        return Response({'team_id': team_id, 'meta': meta, 'season_avgs': avgs, 'last_10': logs})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ── 6. Player Stats ──────────────────────────────────────────────────────────
@api_view(['GET'])
def player_stats(request, player_id):
    try:
        # Player profile
        p_res = supabase.table('players').select('*').eq('player_id', player_id).single().execute()
        player = p_res.data
        team_meta = TEAM_META.get(player.get('team_id'), {})

        # Season averages from view
        avg_res = supabase.table('player_season_avgs').select('*').eq('player_id', player_id).execute()
        avgs = avg_res.data[0] if avg_res.data else {}

        # Game log (last 15)
        log_res = supabase.table('player_game_logs') \
            .select('game_id, game_date, pts, reb, ast, stl, blk, fg_pct, fg3_pct, min_played, plus_minus, win, opp_team_id, is_home') \
            .eq('player_id', player_id).order('game_date', desc=True).limit(15).execute()
        logs = [{
            **g,
            'opp_abbrev': TEAM_META.get(g.get('opp_team_id'), {}).get('abbrev', '???'),
        } for g in log_res.data]

        return Response({'player': player, 'team_meta': team_meta, 'season_avgs': avgs, 'game_log': logs})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ── 7. Player Search ─────────────────────────────────────────────────────────
@api_view(['GET'])
def player_search(request):
    q = request.query_params.get('q', '').strip()
    if len(q) < 2:
        return Response({'results': []})
    try:
        res = supabase.table('players').select('player_id, full_name, team_id, position, is_active') \
            .ilike('full_name', f'%{q}%').eq('is_active', True).limit(10).execute()
        results = [{**r, 'team_abbrev': TEAM_META.get(r['team_id'], {}).get('abbrev', '')} for r in res.data]
        return Response({'results': results})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ── 8. League Leaders ────────────────────────────────────────────────────────
@api_view(['GET'])
def league_leaders(request):
    stat = request.query_params.get('stat', 'pts_avg')
    allowed = {'pts_avg', 'reb_avg', 'ast_avg', 'fg_pct_avg', 'fg3_pct_avg'}
    if stat not in allowed:
        stat = 'pts_avg'
    try:
        res = supabase.table('player_season_avgs').select('*') \
            .order(stat, desc=True).limit(20).execute()
        leaders = [{**r, 'team_abbrev': TEAM_META.get(r['team_id'], {}).get('abbrev', ''), 'team_accent': TEAM_META.get(r['team_id'], {}).get('accent', '#6c63ff')} for r in res.data]
        return Response({'stat': stat, 'leaders': leaders})
    except Exception as e:
        return Response({'error': str(e)}, status=500)
