"""Thin psycopg2 helper for the v2 API (pooled, returns plain dicts with JSON-safe numbers)."""
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../ml'))
from features import connect  # noqa: E402

_pool = None
_lock = threading.Lock()

REGULAR = "('Regular Season','NBA Emirates Cup')"   # the Cup final ('Emirates NBA Cup') does not count toward records
# season in Basketball-Reference convention: 2026 == 2025-26
SEASON_SQL = "(EXTRACT(YEAR FROM (game_date - INTERVAL '6 months'))::int + 1)"


def season_label(season: int) -> str:
    return f"{season - 1}-{str(season)[2:]}"


def _clean(v):
    if isinstance(v, Decimal):
        return float(v)
    return v


def query(sql, params=None):
    global _pool
    with _lock:
        if _pool is None:
            _pool = ThreadedConnectionPool(4, 6, **_conn_kwargs())   # minconn: psycopg2 closes anything above it on release and a reconnect costs ~2 s; Supabase's session pooler allows only 15 clients in total, shared with scripts + CI
    conn = _pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall() if cur.description else []
        conn.commit()
        return [{k: _clean(v) for k, v in r.items()} for r in rows]
    except psycopg2.Error:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None


def _conn_kwargs():
    """Pool needs kwargs; reuse the same env resolution as ml.features.connect()."""
    url = os.environ.get('DATABASE_URL')
    if url:
        return {'dsn': url, 'sslmode': 'require'}
    return dict(host=os.environ['SUPABASE_DB_HOST'], port=os.environ['SUPABASE_DB_PORT'],
                dbname=os.environ['SUPABASE_DB_NAME'], user=os.environ.get('SUPABASE_DB_USER', 'postgres'),
                password=os.environ['SUPABASE_DB_PASSWORD'], sslmode='require')


_season_cache = [0, None]


def current_season() -> int:
    """Newest season where some team has played >= 10 regular-season games (cached 5 min)."""
    if _season_cache[1] is not None and time.time() - _season_cache[0] < 300:
        return _season_cache[1]
    _season_cache[:] = [time.time(), _current_season_uncached()]
    return _season_cache[1]


def _current_season_uncached() -> int:
    row = one(f"""SELECT MAX(season) AS s FROM (
                    SELECT {SEASON_SQL} AS season, team_id, COUNT(*) n FROM team_game_stats
                    WHERE COALESCE(game_type,'Regular Season') IN {REGULAR} GROUP BY 1, 2 HAVING COUNT(*) >= 10) x""")
    return int(row['s'])


_executor = ThreadPoolExecutor(4)


def parallel(*specs):
    """Run several (sql, params) queries concurrently. The DB is ~300 ms away, so N serial queries cost N round trips."""
    futures = [_executor.submit(query, sql, params) for sql, params in specs]
    return [f.result() for f in futures]


_cache = {}


def ttl_cache(seconds):
    """Cache a DRF view's payload per full URL (sits under @api_view, so we cache .data, not the Response).
    Pages are read-mostly and the sync jobs only run every few minutes anyway."""
    def deco(fn):
        @wraps(fn)
        def wrapper(request, *args, **kwargs):
            from rest_framework.response import Response
            key = request.get_full_path()
            hit = _cache.get(key)
            if hit and time.time() - hit[0] < seconds:
                return Response(hit[1])
            resp = fn(request, *args, **kwargs)
            if getattr(resp, 'status_code', 200) == 200:
                _cache[key] = (time.time(), resp.data)
            return resp
        return wrapper
    return deco
