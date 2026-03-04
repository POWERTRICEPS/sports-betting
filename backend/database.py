import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from collections import OrderedDict
import os
from dotenv import load_dotenv

load_dotenv()

# Render database config
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    from urllib.parse import urlparse
    
    result = urlparse(DATABASE_URL)
    DB_CONFIG = {
        'host': result.hostname,
        'port': result.port or 5432,
        'database': result.path[1:],  
        'user': result.username,
        'password': result.password
    }
    print(f"Using Render database: {result.hostname}")
else:
    # local database env variables
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'sports_betting'),
        'user': os.getenv('DB_USER', 'junhyungyoon'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    print(f"💻 Using local database: {DB_CONFIG['host']}")

def get_db_connection():
    """Creates database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


@contextmanager
def get_db():
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_query(query, params=None, fetch_one=False):
    """
    select query
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch_one:
                return cur.fetchone()
            return cur.fetchall()


def execute_insert(query, params=None):
    """
    insert query and returns the inserted id.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            return result[list(result.keys())[0]] if result else None


def execute_update(query, params=None):
    """
    update or delete queries.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount


def test_connection():
    """Test database connection"""
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                print("Postgres database connection successful!")
                return True
    except Exception as e:
        print("Postgres database connection failed!")
        print(f"Error: {e}")
        return False


def _fetch_game_history_sync(
    order: str = "desc",
    limit: int | None = None,
    date: str | None = None,
) -> list[dict]:
    """
    Synchronous helper that queries past_game_info sorted by game_date,
    then groups the results into one entry per day.

    Args:
        order: 'desc' (newest first, default) or 'asc' (oldest first).
        limit:  Max rows to return (applied before grouping).  None = all rows.
        date:   Optional 'YYYY-MM-DD' string.  If provided, only games on
                that date are returned.

    Returns:
        List of dicts, each shaped as:
            { "date": "2026-03-04", "games": [ ...game dicts... ] }
        The outer list is ordered by date according to *order*.
    """
    direction = "ASC" if order.lower() == "asc" else "DESC"
    params: list = []

    where_clause = ""
    if date is not None:
        where_clause = "WHERE game_date = %s"
        params.append(date)

    query = f"""
        SELECT
            past_game_id,
            game_date,
            home_team,
            home_team_score,
            away_team,
            away_team_score,
            game_time_elapsed,
            game_stadium,
            home_win_probability,
            away_win_probability,
            probability_last_updated
        FROM past_game_info
        {where_clause}
        ORDER BY game_date {direction}
    """
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)

    rows = execute_query(query, tuple(params) if params else None)

    # Group rows by game_date (preserves query order via OrderedDict)
    grouped: OrderedDict[str, list[dict]] = OrderedDict()
    for row in rows:
        date_key = str(row["game_date"])
        grouped.setdefault(date_key, []).append(dict(row))

    return [{"date": date, "games": games} for date, games in grouped.items()]


async def fetch_game_history(
    order: str = "desc",
    limit: int | None = None,
    date: str | None = None,
) -> list[dict]:
    """
    Async wrapper around the game history query.

    Runs the synchronous psycopg2 call in a thread so it doesn't block
    the FastAPI event loop.  Handles connection timeouts gracefully.

    Args:
        order: 'desc' (newest first, default) or 'asc' (oldest first).
        limit:  Max rows to return (before grouping).  None = all rows.
        date:   Optional 'YYYY-MM-DD'.  If provided, returns only that day.

    Returns:
        List of { "date": "YYYY-MM-DD", "games": [...] } dicts,
        one entry per day, ordered by date.

    Raises:
        Exception with a descriptive message on connection timeout or
        other database errors.
    """
    import asyncio

    try:
        return await asyncio.to_thread(_fetch_game_history_sync, order, limit, date)
    except psycopg2.OperationalError as e:
        raise Exception(f"Database connection timeout or operational error: {e}")
    except Exception as e:
        raise Exception(f"Failed to fetch game history: {e}")


_FINAL_STATUSES = {"final", "game over", "f/ot", "f/2ot"}  # ESPN shortDetail values


def _is_final(status: str) -> bool:
    """Return True if the ESPN status string indicates a completed game."""
    return status.strip().lower() in _FINAL_STATUSES or status.strip().lower().startswith("final")


def _save_completed_games_sync(games_with_probs: list[dict]) -> int:
    """
    Synchronous helper: upserts completed games into past_game_info.

    Only games whose status is 'Final' (or equivalent) are written.
    Uses INSERT ... ON CONFLICT DO UPDATE so re-running is idempotent.

    Args:
        games_with_probs: merged game dicts from merge_gp() — includes
            game_id, status, home/away team, scores, and win probabilities.

    Returns:
        Number of rows upserted.
    """
    from datetime import date

    completed = [g for g in games_with_probs if _is_final(g.get("status", ""))]
    if not completed:
        return 0

    upserted = 0
    with get_db() as conn:
        with conn.cursor() as cur:
            for g in completed:
                cur.execute(
                    """
                    INSERT INTO past_game_info (
                        past_game_id,
                        game_date,
                        home_team,
                        home_team_score,
                        away_team,
                        away_team_score,
                        game_time_elapsed,
                        game_stadium,
                        home_win_probability,
                        away_win_probability,
                        probability_last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (past_game_id) DO UPDATE SET
                        home_team_score        = EXCLUDED.home_team_score,
                        away_team_score        = EXCLUDED.away_team_score,
                        home_win_probability   = EXCLUDED.home_win_probability,
                        away_win_probability   = EXCLUDED.away_win_probability,
                        probability_last_updated = NOW()
                    """,
                    (
                        int(g["game_id"]),
                        date.today(),
                        g.get("home_team", ""),
                        int(g.get("home_score", 0) or 0),
                        g.get("away_team", ""),
                        int(g.get("away_score", 0) or 0),
                        "00:48:00",          # regulation length placeholder
                        g.get("home_city", ""),
                        float(g.get("home_win_prob") or 0.5),
                        float(g.get("away_win_prob") or 0.5),
                    ),
                )
                upserted += 1
    return upserted


async def save_completed_games_to_db(games_with_probs: list[dict]) -> int:
    """
    Async wrapper: persists any finished games from the current poll cycle
    into the past_game_info table on the Render Postgres database.

    Safe to call every 5 s — only final games are written and the upsert
    is idempotent, so duplicate calls for the same game_id are harmless.

    Args:
        games_with_probs: the merged list returned by merge_gp().

    Returns:
        Number of rows upserted (0 if no games are final yet).
    """
    import asyncio

    try:
        count = await asyncio.to_thread(_save_completed_games_sync, games_with_probs)
        if count:
            print(f"[db] saved {count} completed game(s) to past_game_info")
        return count
    except psycopg2.OperationalError as e:
        print(f"[db] connection error while saving games: {e}")
        return 0
    except Exception as e:
        print(f"[db] failed to save completed games: {e}")
        return 0


if __name__ == "__main__":
    test_connection()
