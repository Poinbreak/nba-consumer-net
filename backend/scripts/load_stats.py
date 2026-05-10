"""
Loads TeamStatistics.csv and PlayerStatistics.csv into Supabase.
Only processes the last 2 seasons worth of data for speed (2024+).
"""
import os
import math
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
supabase: Client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')


def clean(val):
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    return val


def clean_records(records):
    return [{k: clean(v) for k, v in r.items()} for r in records]


def upsert(table, records, chunk=500):
    records = clean_records(records)
    total = len(records)
    for i in range(0, total, chunk):
        supabase.table(table).upsert(records[i:i+chunk]).execute()
        print(f"  {min(i+chunk, total)}/{total}")


# ── 1. team_game_stats ──────────────────────────────────────────────────────
def load_team_stats():
    print("\n── Loading team game stats …")
    df = pd.read_csv(os.path.join(DATA_DIR, 'TeamStatistics.csv'), low_memory=False)
    df['gameDate'] = pd.to_datetime(df['gameDate'])
    df = df[df['gameDate'].dt.year >= 2023]   # last 2+ seasons

    # Compute derived fields
    fga  = df['fieldGoalsAttempted'].replace(0, 1)
    fta  = df['freeThrowsAttempted'].replace(0, 1)
    reb  = df['reboundsTotal']
    oreb = df['reboundsOffensive']
    dreb = df['reboundsDefensive']
    tov  = df['turnovers']
    poss = fga + 0.44 * fta - oreb + tov   # simplified possessions

    df['efg_pct']    = (df['fieldGoalsMade'] + 0.5 * df['threePointersMade']) / fga
    df['tov_pct']    = tov / poss.replace(0, 1)
    df['oreb_pct']   = oreb / (oreb + dreb).replace(0, 1)
    df['ft_rate']    = fta / fga

    records = []
    for _, r in df.iterrows():
        records.append({
            'game_id':    str(int(r['gameId'])),
            'team_id':    int(r['teamId']),
            'opp_team_id': int(r['opponentTeamId']),
            'is_home':    bool(r['home']),
            'win':        bool(r['win']) if not math.isnan(r['win']) else None,
            'pts':        int(r['teamScore']) if not math.isnan(r['teamScore']) else None,
            'opp_pts':    int(r['opponentScore']) if not math.isnan(r['opponentScore']) else None,
            'ast':        int(r['assists']) if not math.isnan(r['assists']) else None,
            'blk':        int(r['blocks']) if not math.isnan(r['blocks']) else None,
            'stl':        int(r['steals']) if not math.isnan(r['steals']) else None,
            'fga':        int(r['fieldGoalsAttempted']) if not math.isnan(r['fieldGoalsAttempted']) else None,
            'fgm':        int(r['fieldGoalsMade']) if not math.isnan(r['fieldGoalsMade']) else None,
            'fg_pct':     round(float(r['fieldGoalsPercentage']), 4) if not math.isnan(r['fieldGoalsPercentage']) else None,
            'fg3a':       int(r['threePointersAttempted']) if not math.isnan(r['threePointersAttempted']) else None,
            'fg3m':       int(r['threePointersMade']) if not math.isnan(r['threePointersMade']) else None,
            'fg3_pct':    round(float(r['threePointersPercentage']), 4) if not math.isnan(r['threePointersPercentage']) else None,
            'fta':        int(r['freeThrowsAttempted']) if not math.isnan(r['freeThrowsAttempted']) else None,
            'ftm':        int(r['freeThrowsMade']) if not math.isnan(r['freeThrowsMade']) else None,
            'ft_pct':     round(float(r['freeThrowsPercentage']), 4) if not math.isnan(r['freeThrowsPercentage']) else None,
            'reb':        int(r['reboundsTotal']) if not math.isnan(r['reboundsTotal']) else None,
            'oreb':       int(r['reboundsOffensive']) if not math.isnan(r['reboundsOffensive']) else None,
            'dreb':       int(r['reboundsDefensive']) if not math.isnan(r['reboundsDefensive']) else None,
            'tov':        int(r['turnovers']) if not math.isnan(r['turnovers']) else None,
            'pf':         int(r['foulsPersonal']) if not math.isnan(r['foulsPersonal']) else None,
            'pts_paint':  int(r['pointsInThePaint']) if not math.isnan(r['pointsInThePaint']) else None,
            'pts_fb':     int(r['pointsFastBreak']) if not math.isnan(r['pointsFastBreak']) else None,
            'bench_pts':  int(r['benchPoints']) if not math.isnan(r['benchPoints']) else None,
            'efg_pct':    round(float(r['efg_pct']), 4) if not math.isnan(r['efg_pct']) else None,
            'tov_pct':    round(float(r['tov_pct']), 4) if not math.isnan(r['tov_pct']) else None,
            'oreb_pct':   round(float(r['oreb_pct']), 4) if not math.isnan(r['oreb_pct']) else None,
            'ft_rate':    round(float(r['ft_rate']), 4) if not math.isnan(r['ft_rate']) else None,
            'plus_minus': float(r['plusMinusPoints']) if not math.isnan(r['plusMinusPoints']) else None,
            'season_wins': int(r['seasonWins']) if not math.isnan(r['seasonWins']) else None,
            'season_losses': int(r['seasonLosses']) if not math.isnan(r['seasonLosses']) else None,
            'game_date':  r['gameDate'].strftime('%Y-%m-%d'),
            'game_type':  str(r['gameType']) if pd.notna(r['gameType']) else None,
        })

    print(f"  Inserting {len(records)} team game rows …")
    upsert('team_game_stats', records)


# ── 2. player_game_logs ─────────────────────────────────────────────────────
def load_player_stats():
    print("\n── Loading player game stats …")
    df = pd.read_csv(os.path.join(DATA_DIR, 'PlayerStatistics.csv'), low_memory=False)
    df['gameDate'] = pd.to_datetime(df['gameDate'])
    df = df[df['gameDate'].dt.year >= 2024]  # current + last season only (keeps volume manageable)
    # Exclude DNP rows (no minutes)
    df = df[df['numMinutes'].notna() & (df['numMinutes'] > 0)]

    records = []
    for _, r in df.iterrows():
        records.append({
            'player_id':  int(r['personId']),
            'game_id':    str(int(r['gameId'])),
            'team_id':    int(r['playerteamId']),
            'opp_team_id': int(r['opponentteamId']),
            'is_home':    bool(r['home']),
            'win':        bool(r['win']),
            'min':        round(float(r['numMinutes']), 2),
            'pts':        int(r['points']),
            'ast':        int(r['assists']),
            'blk':        int(r['blocks']),
            'stl':        int(r['steals']),
            'fga':        int(r['fieldGoalsAttempted']),
            'fgm':        int(r['fieldGoalsMade']),
            'fg_pct':     round(float(r['fieldGoalsPercentage']), 4) if not math.isnan(r['fieldGoalsPercentage']) else None,
            'fg3a':       int(r['threePointersAttempted']),
            'fg3m':       int(r['threePointersMade']),
            'fg3_pct':    round(float(r['threePointersPercentage']), 4) if not math.isnan(r['threePointersPercentage']) else None,
            'fta':        int(r['freeThrowsAttempted']),
            'ftm':        int(r['freeThrowsMade']),
            'ft_pct':     round(float(r['freeThrowsPercentage']), 4) if not math.isnan(r['freeThrowsPercentage']) else None,
            'reb':        int(r['reboundsTotal']),
            'oreb':       int(r['reboundsOffensive']),
            'dreb':       int(r['reboundsDefensive']),
            'tov':        int(r['turnovers']),
            'pf':         int(r['foulsPersonal']),
            'plus_minus': float(r['plusMinusPoints']) if not math.isnan(r['plusMinusPoints']) else None,
            'is_started': str(r['startingPosition']) != 'nan' and str(r['startingPosition']) != '',
            'game_date':  r['gameDate'].strftime('%Y-%m-%d'),
            'game_type':  str(r['gameType']) if pd.notna(r['gameType']) else None,
        })

    print(f"  Inserting {len(records)} player game rows …")
    upsert('player_game_logs', records, chunk=300)


if __name__ == '__main__':
    load_team_stats()
    load_player_stats()
    print("\n✅ Done loading stats from CSV.")
