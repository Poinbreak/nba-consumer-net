import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')

def chunked_upsert(table_name: str, df: pd.DataFrame, chunk_size: int = 1000):
    # Fill NaN with None directly in the dataframe using modern pandas
    df = df.astype(object).where(pd.notnull(df), None)
    records = df.to_dict(orient='records')
    # Extra safety: iterate and fix any remaining nan/inf
    import math
    for r in records:
        for k, v in r.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                r[k] = None
    total = len(records)
    print(f"Upserting {total} records into {table_name}...")
    for i in range(0, total, chunk_size):
        chunk = records[i:i+chunk_size]
        response = supabase.table(table_name).upsert(chunk).execute()
        print(f"Processed {min(i+chunk_size, total)}/{total}")

def bootstrap_teams():
    print("Bootstrapping Teams...")
    df = pd.read_csv(os.path.join(DATA_DIR, 'TeamHistories.csv'))
    # Only keep latest iteration of each team (active till 2100) or just unique teamIds
    # We will sort by seasonActiveTill descending and drop duplicates
    df = df.sort_values('seasonActiveTill', ascending=False).drop_duplicates('teamId')
    
    teams_df = pd.DataFrame({
        'team_id': df['teamId'],
        'full_name': df['teamCity'].fillna('') + ' ' + df['teamName'].fillna(''),
        'abbreviation': df['teamAbbrev'].str.strip(),
        'city': df['teamCity'],
        'conference': None,  # Not in dataset
        'division': None,    # Not in dataset
        'is_active': df['seasonActiveTill'] >= 2100
    })
    
    # Filter out teams not in TeamHistories to prevent FK constraint errors
    valid_team_ids = set(df['teamId'])
    return valid_team_ids

def bootstrap_players(valid_team_ids):
    print("Bootstrapping Players...")
    df = pd.read_csv(os.path.join(DATA_DIR, 'Players.csv'))
    
    players_df = pd.DataFrame({
        'player_id': df['personId'],
        'full_name': df['firstName'].fillna('') + ' ' + df['lastName'].fillna(''),
        'team_id': None,  # Will update later
        'position': None, # Will extract from stats
        'age': None,
        'jersey_number': df['jersey'].astype(str).str.replace(r'\.0$', '', regex=True).str.replace('nan', '').str.replace('None', '').str.slice(0, 5),
        'is_active': df['toYear'] >= 2024,
        'is_custom': False
    })
    
    # Replace empty strings with None
    players_df['jersey_number'] = players_df['jersey_number'].replace('', None)
    
    # Replace NaN with None
    players_df = players_df.where(pd.notnull(players_df), None)
    chunked_upsert('players', players_df, chunk_size=2000)

def bootstrap_games(valid_team_ids):
    print("Bootstrapping Games (last 5 years for speed)...")
    df = pd.read_csv(os.path.join(DATA_DIR, 'Games.csv'), low_memory=False)
    
    # Filter to recent games to avoid massive payload initially
    df['gameDate'] = pd.to_datetime(df['gameDate'])
    df = df[df['gameDate'].dt.year >= 2019]
    
    games_df = pd.DataFrame({
        'game_id': df['gameId'].astype(str),
        'season_id': None,  # Need seasons table first
        'game_date': df['gameDate'].dt.strftime('%Y-%m-%d'),
        'home_team_id': df['hometeamId'],
        'away_team_id': df['awayteamId'],
        'home_score': df['homeScore'],
        'away_score': df['awayScore'],
        'status': 'Final',  # Historical games are final
        'home_days_rest': None, # Calculated in nightly ingest
        'away_days_rest': None,
        'quarter': 4,
        'time_remaining': '0:00'
    })
    
    # Filter to valid teams
    games_df = games_df[games_df['home_team_id'].isin(valid_team_ids) & games_df['away_team_id'].isin(valid_team_ids)]
    
    games_df = games_df.where(pd.notnull(games_df), None)
    chunked_upsert('games', games_df, chunk_size=2000)

if __name__ == "__main__":
    print("Starting Kaggle Bootstrap...")
    try:
        valid_teams = bootstrap_teams()
        bootstrap_players(valid_teams)
        bootstrap_games(valid_teams)
        print("Initial Bootstrap Complete! Note: Team and Player Stats skipped to avoid exceeding API limits. Run nightly ingest to compute rolling stats.")
    except Exception as e:
        print(f"Error during bootstrap: {e}")
