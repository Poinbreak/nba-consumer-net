"""
Bulk-load Kaggle CSVs into Postgres via COPY (direct DB connection, ~100x faster than REST upserts).

Loads team_game_stats (with computed off/def/net rating + pace + quarter points) and
player_game_logs for every game already present in `games`. Idempotent: ON CONFLICT DO NOTHING
on (game_id, team_id) / (game_id, player_id).

    python scripts/bulk_load.py [team|player|all]
"""
import io
import os
import sys

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')


def connect():
    return psycopg2.connect(
        host=os.environ['SUPABASE_DB_HOST'], port=os.environ['SUPABASE_DB_PORT'],
        dbname=os.environ['SUPABASE_DB_NAME'], user=os.environ.get('SUPABASE_DB_USER', 'postgres'),
        password=os.environ['SUPABASE_DB_PASSWORD'], sslmode='require',
    )


def copy_upsert(conn, df, table, cols, conflict):
    """COPY df into a temp table, then INSERT .. ON CONFLICT DO NOTHING into `table`."""
    df = df[cols]
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, na_rep='\\N')
    buf.seek(0)
    with conn.cursor() as cur:
        cur.execute(f"CREATE TEMP TABLE _stage (LIKE {table} INCLUDING DEFAULTS) ON COMMIT DROP")
        col_sql = ', '.join(cols)
        cur.copy_expert(f"COPY _stage ({col_sql}) FROM STDIN WITH (FORMAT csv, NULL '\\N')", buf)
        cur.execute(
            f"INSERT INTO {table} ({col_sql}) SELECT {col_sql} FROM _stage "
            f"ON CONFLICT ({conflict}) DO NOTHING"
        )
        n = cur.rowcount
    conn.commit()
    print(f"  {table}: inserted {n} of {len(df)} rows")


def known_ids(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT game_id FROM games")
        games = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT team_id FROM teams")
        teams = {r[0] for r in cur.fetchall()}
        cur.execute("SELECT player_id FROM players")
        players = {r[0] for r in cur.fetchall()}
    return games, teams, players


def load_team_stats(conn):
    print("── team_game_stats")
    games, teams, _ = known_ids(conn)
    df = pd.read_csv(os.path.join(DATA_DIR, 'TeamStatistics.csv'), low_memory=False)
    df['game_id'] = df['gameId'].astype(str)
    df = df[df['game_id'].isin(games)].copy()
    df = df[df['teamId'].isin(teams) & df['opponentTeamId'].isin(teams)].copy()
    df = df.reset_index(drop=True)
    df['teamId'] = df['teamId'].astype('int64')
    df['opponentTeamId'] = df['opponentTeamId'].astype('int64')

    fga, fta, oreb, tov = df['fieldGoalsAttempted'], df['freeThrowsAttempted'], df['reboundsOffensive'], df['turnovers']
    df['poss'] = fga + 0.44 * fta - oreb + tov
    opp_poss = df[['game_id', 'teamId', 'poss']].rename(columns={'teamId': 'opponentTeamId', 'poss': 'opp_poss'})
    df = df.merge(opp_poss, on=['game_id', 'opponentTeamId'], how='left')
    fga, fta, oreb, tov = df['fieldGoalsAttempted'], df['freeThrowsAttempted'], df['reboundsOffensive'], df['turnovers']
    avg_poss = ((df['poss'] + df['opp_poss'].fillna(df['poss'])) / 2).replace(0, pd.NA)

    safe_fga = fga.replace(0, pd.NA)
    df['efg_pct'] = (df['fieldGoalsMade'] + 0.5 * df['threePointersMade']) / safe_fga
    df['tov_pct'] = tov / df['poss'].replace(0, pd.NA)
    df['oreb_pct'] = oreb / (oreb + df['reboundsDefensive']).replace(0, pd.NA)
    df['ft_rate'] = fta / safe_fga
    df['off_rating'] = 100 * df['teamScore'] / avg_poss
    df['def_rating'] = 100 * df['opponentScore'] / avg_poss
    df['net_rating'] = df['off_rating'] - df['def_rating']
    df['pace'] = avg_poss * 48 / (df['numMinutes'].where(df['numMinutes'] > 0, 240) / 5)

    out = pd.DataFrame({
        'game_id': df['game_id'], 'team_id': df['teamId'].astype('int64'), 'opp_team_id': df['opponentTeamId'].astype('int64'),
        'is_home': df['home'].astype(bool), 'win': df['win'].astype('boolean'),
        'pts': df['teamScore'], 'opp_pts': df['opponentScore'],
        'reb': df['reboundsTotal'], 'ast': df['assists'], 'stl': df['steals'], 'blk': df['blocks'],
        'tov': tov, 'fgm': df['fieldGoalsMade'], 'fga': fga, 'fg3m': df['threePointersMade'],
        'fg3a': df['threePointersAttempted'], 'ftm': df['freeThrowsMade'], 'fta': fta,
        'fg_pct': df['fieldGoalsPercentage'], 'fg3_pct': df['threePointersPercentage'],
        'ft_pct': df['freeThrowsPercentage'], 'oreb': oreb, 'dreb': df['reboundsDefensive'],
        'pf': df['foulsPersonal'], 'pts_fb': df['pointsFastBreak'],
        'pts_paint': df.get('pointsInThePaint'), 'bench_pts': df['benchPoints'],
        'plus_minus': df['plusMinusPoints'],
        'efg_pct': df['efg_pct'], 'tov_pct': df['tov_pct'], 'oreb_pct': df['oreb_pct'], 'ft_rate': df['ft_rate'],
        'off_rating': df['off_rating'], 'def_rating': df['def_rating'], 'net_rating': df['net_rating'],
        'pace': df['pace'],
        'q1_pts': df['q1Points'], 'q2_pts': df['q2Points'], 'q3_pts': df['q3Points'], 'q4_pts': df['q4Points'],
        'game_date': pd.to_datetime(df['gameDateTimeEst'], utc=True, errors='coerce').dt.strftime('%Y-%m-%d'),
        'game_type': df['gameType'],
    })
    # Round to column scale; numeric(5,4) overflows on stray values > 9.9999
    for c in ['efg_pct', 'tov_pct', 'oreb_pct', 'ft_rate', 'fg_pct', 'fg3_pct', 'ft_pct']:
        out[c] = out[c].astype(float).clip(0, 9.9999).round(4)
    for c in ['off_rating', 'def_rating', 'net_rating', 'pace', 'plus_minus']:
        out[c] = out[c].astype(float).clip(-9999, 9999).round(2)
    int_cols = ['pts', 'opp_pts', 'reb', 'ast', 'stl', 'blk', 'tov', 'fgm', 'fga', 'fg3m', 'fg3a', 'ftm', 'fta',
                'oreb', 'dreb', 'pf', 'pts_fb', 'pts_paint', 'bench_pts', 'q1_pts', 'q2_pts', 'q3_pts', 'q4_pts']
    for c in int_cols:
        out[c] = pd.to_numeric(out[c], errors='coerce').round().astype('Int64')
    out['is_home'] = out['is_home'].map({True: 't', False: 'f'})
    out['win'] = out['win'].map({True: 't', False: 'f'})
    out = out.drop_duplicates(['game_id', 'team_id'])
    copy_upsert(conn, out, 'team_game_stats', list(out.columns), 'game_id, team_id')


def load_player_stats(conn):
    print("── player_game_logs")
    games, teams, players = known_ids(conn)
    df = pd.read_csv(os.path.join(DATA_DIR, 'PlayerStatistics.csv'), low_memory=False)
    df['game_id'] = df['gameId'].astype(str)
    df = df[df['game_id'].isin(games) & df['personId'].isin(players)]
    df = df[df['playerteamId'].isin(teams) & df['opponentteamId'].isin(teams)]
    df['numMinutes'] = pd.to_numeric(df['numMinutes'], errors='coerce')
    df = df[df['numMinutes'].notna() & (df['numMinutes'] > 0)].copy()
    for c in ['personId', 'playerteamId', 'opponentteamId']:
        df[c] = df[c].astype('int64')

    out = pd.DataFrame({
        'game_id': df['game_id'], 'player_id': df['personId'], 'team_id': df['playerteamId'],
        'opp_team_id': df['opponentteamId'],
        'win': df['win'].astype(bool).map({True: 't', False: 'f'}),
        'min': df['numMinutes'].round(2), 'min_played': df['numMinutes'].round(2),
        'pts': df['points'], 'reb': df['reboundsTotal'], 'ast': df['assists'], 'stl': df['steals'],
        'blk': df['blocks'], 'tov': df['turnovers'], 'fgm': df['fieldGoalsMade'], 'fga': df['fieldGoalsAttempted'],
        'fg3m': df['threePointersMade'], 'fg3a': df['threePointersAttempted'],
        'ftm': df['freeThrowsMade'], 'fta': df['freeThrowsAttempted'],
        'fg_pct': df['fieldGoalsPercentage'].clip(0, 1).round(4),
        'fg3_pct': df['threePointersPercentage'].clip(0, 1).round(4),
        'ft_pct': df['freeThrowsPercentage'].clip(0, 1).round(4),
        'oreb': df['reboundsOffensive'], 'dreb': df['reboundsDefensive'], 'pf': df['foulsPersonal'],
        'plus_minus': df['plusMinusPoints'].round(2),
        'is_started': df['startingPosition'].notna() & (df['startingPosition'].astype(str) != ''),
        'game_date': pd.to_datetime(df['gameDateTimeEst'], utc=True, errors='coerce').dt.strftime('%Y-%m-%d'),
        'game_type': df['gameType'],
    })
    out['is_started'] = out['is_started'].map({True: 't', False: 'f'})
    for c in ['pts', 'reb', 'ast', 'stl', 'blk', 'tov', 'fgm', 'fga', 'fg3m', 'fg3a', 'ftm', 'fta', 'oreb', 'dreb', 'pf']:
        out[c] = pd.to_numeric(out[c], errors='coerce').round().astype('Int64')
    out = out.drop_duplicates(['game_id', 'player_id'])
    for i in range(0, len(out), 100_000):
        copy_upsert(conn, out.iloc[i:i + 100_000], 'player_game_logs', list(out.columns), 'game_id, player_id')


if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    conn = connect()
    if what in ('team', 'all'):
        load_team_stats(conn)
    if what in ('player', 'all'):
        load_player_stats(conn)
    print("✅ done")
