import os
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
from nba_api.stats.endpoints import scoreboardv2, teamgamelogs, playergamelogs
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_yesterdays_games(target_date=None):
    """Fetch yesterday's results from nba_api and upsert to games table."""
    if not target_date:
        target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"Fetching scoreboard for {target_date}...")
    board = scoreboardv2.ScoreboardV2(game_date=target_date)
    games = board.get_data_frames()[0]
    
    records = []
    for _, row in games.iterrows():
        # Scoreboard data is somewhat complex, this is simplified for brevity
        # nba_api scoreboard returns HOME_TEAM_ID, VISITOR_TEAM_ID, etc.
        records.append({
            'game_id': str(row['GAME_ID']),
            'game_date': target_date,
            'home_team_id': row['HOME_TEAM_ID'],
            'away_team_id': row['VISITOR_TEAM_ID'],
            'status': row['GAME_STATUS_TEXT'], # 'Final'
        })
    
    if records:
        supabase.table('games').upsert(records).execute()
        print(f"Upserted {len(records)} games.")

def compute_days_rest(team_id: int, game_date: str) -> int:
    """Calculate days_rest for a specific team before a specific game date."""
    try:
        res = supabase.table('games').select('game_date') \
            .or_(f"home_team_id.eq.{team_id},away_team_id.eq.{team_id}") \
            .lt('game_date', game_date) \
            .eq('status', 'Final') \
            .order('game_date', desc=True) \
            .limit(1).execute()
            
        if not res.data:
            return 7 # Cap at 7 days rest
            
        prev_date = pd.to_datetime(res.data[0]['game_date'])
        curr_date = pd.to_datetime(game_date)
        delta = (curr_date - prev_date).days
        return min(delta, 7)
    except Exception as e:
        print(f"Error computing days rest: {e}")
        return 7

def process_missing_days_rest():
    print("Computing days rest for missing games...")
    res = supabase.table('games').select('game_id, home_team_id, away_team_id, game_date').is_('home_days_rest', 'null').limit(100).execute()
    
    updates = []
    for row in res.data:
        home_rest = compute_days_rest(row['home_team_id'], row['game_date'])
        away_rest = compute_days_rest(row['away_team_id'], row['game_date'])
        updates.append({
            'game_id': row['game_id'],
            'home_days_rest': home_rest,
            'away_days_rest': away_rest
        })
        
    if updates:
        supabase.table('games').upsert(updates).execute()
        print(f"Updated days rest for {len(updates)} games.")

def compute_team_rolling(team_id: int, window: int):
    """Compute 5 and 10 game rolling averages for a team."""
    res = supabase.table('team_game_stats').select('*') \
        .eq('team_id', team_id) \
        .order('id', desc=True) \
        .limit(window).execute()
        
    if len(res.data) < window:
        return None
        
    df = pd.DataFrame(res.data)
    
    return {
        'team_id': team_id,
        'as_of_date': datetime.now().strftime('%Y-%m-%d'),
        'stat_window': window,
        'efg_pct_roll': df['efg_pct'].mean() if 'efg_pct' in df else None,
        'tov_pct_roll': df['tov_pct'].mean() if 'tov_pct' in df else None,
        'oreb_pct_roll': df['oreb_pct'].mean() if 'oreb_pct' in df else None,
        'ft_rate_roll': df['ft_rate'].mean() if 'ft_rate' in df else None,
        'net_rating_roll': df['net_rating'].mean() if 'net_rating' in df else None,
        'off_rating_roll': df['off_rating'].mean() if 'off_rating' in df else None,
        'def_rating_roll': df['def_rating'].mean() if 'def_rating' in df else None,
        'pace_roll': df['pace'].mean() if 'pace' in df else None,
        'fga_avg_roll': df['fga'].mean() if 'fga' in df else None
    }

def cluster_teams():
    """Run K-Means clustering on team defensive stats."""
    print("Clustering teams (K-Means)...")
    # Fetch 10-game rolling def_rating and pace
    response = supabase.table('team_rolling_stats').select('team_id, def_rating_roll, pace_roll').eq('stat_window', 10).execute()
    data = response.data
    
    if len(data) < 5:
        print("Not enough rolling stat data to cluster yet.")
        return
        
    df = pd.DataFrame(data)
    X = df[['def_rating_roll', 'pace_roll']].fillna(0)
    X_scaled = StandardScaler().fit_transform(X)
    
    kmeans = KMeans(n_clusters=5, random_state=42)
    df['cluster_id'] = kmeans.fit_predict(X_scaled)
    
    cluster_labels = {
        0: 'Heavy Rim Protection',
        1: 'Fast Perimeter Hawks',
        2: 'Zone-Heavy Slowdowns',
        3: 'Switch-Heavy Balanced',
        4: 'Soft Defense'
    }
    
    records = []
    for _, row in df.iterrows():
        records.append({
            'team_id': row['team_id'],
            'season_label': '2024-25', # Hardcoded for now
            'cluster_id': row['cluster_id'],
            'cluster_label': cluster_labels.get(row['cluster_id'])
        })
        
    supabase.table('team_defensive_clusters').upsert(records).execute()
    print("K-Means clustering complete.")

if __name__ == "__main__":
    print("Starting Nightly Ingest Pipeline...")
    fetch_yesterdays_games()
    process_missing_days_rest()
    # compute_team_rolling(team_id, 10)
    cluster_teams()
    print("Nightly Ingest Complete.")
