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
            i.past_game_id,
            i.game_date,
            i.home_team,
            i.home_team_score,
            i.away_team,
            i.away_team_score,
            i.game_stadium,
            i.home_win_probability,
            i.away_win_probability,
            i.probability_last_updated,
            s.home_abbreviation,
            s.away_abbreviation,
            s.home_wins,
            s.home_losses,
            s.away_wins,
            s.away_losses
        FROM past_game_info i
        LEFT JOIN past_game_stats s ON i.past_game_id = s.past_game_id
        {where_clause.replace('game_date', 'i.game_date')}
        ORDER BY i.game_date {direction}
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


def past_game_row_to_dashboard_game(row: dict) -> dict:
    """
    Map a past_game_info row to the dashboard game shape.
    """
    gid = str(row["past_game_id"])
    return {
        "game_id": gid,
        "status": "Final",
        "home_team": row.get("home_team", ""),
        "home_city": row.get("game_stadium") or "",
        "home_abbreviation": (row.get("home_abbreviation") or "").strip(),
        "home_wins": int(row.get("home_wins") or 0),
        "home_losses": int(row.get("home_losses") or 0),
        "home_score": int(row.get("home_team_score") or 0),
        "away_team": row.get("away_team", ""),
        "away_city": "",
        "away_abbreviation": (row.get("away_abbreviation") or "").strip(),
        "away_wins": int(row.get("away_wins") or 0),
        "away_losses": int(row.get("away_losses") or 0),
        "away_score": int(row.get("away_team_score") or 0),
    }


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

def is_game_final(game: dict) -> bool:
    """Return True if the game's status indicates a completed game."""
    return "final" in game.get("status", "").lower()


def _save_completed_games_sync(games_with_probs: list[dict]) -> int:
    """
    Upserts completed games into past_game_info (lightweight) and past_game_stats (full).
    Only games whose status is 'Final' are written. past_game_stats is only read when
    the user clicks a game card (get_historical_team_stats).
    """
    from datetime import date

    def _int(v):
        return int(v) if v is not None else None

    def _float(v):
        return float(v) if v is not None else None

    def _str(v):
        return str(v) if v is not None else ""

    completed = [g for g in games_with_probs if is_game_final(g) and g.get("game_id") is not None]
    if not completed:
        return 0

    upserted = 0
    with get_db() as conn:
        with conn.cursor() as cur:
            for g in completed:
                gid = int(g["game_id"])
                game_date = g.get("game_date")
                if hasattr(game_date, "isoformat"):
                    game_date = game_date.isoformat()
                if not game_date:
                    game_date = date.today().isoformat()

                # Lightweight row for listing (game cards)
                cur.execute(
                    """
                    INSERT INTO past_game_info (
                        past_game_id, game_date, home_team, home_team_score,
                        away_team, away_team_score, game_stadium,
                        home_win_probability, away_win_probability, probability_last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (past_game_id) DO UPDATE SET
                        home_team_score = EXCLUDED.home_team_score,
                        away_team_score = EXCLUDED.away_team_score,
                        home_win_probability = EXCLUDED.home_win_probability,
                        away_win_probability = EXCLUDED.away_win_probability,
                        probability_last_updated = NOW()
                    """,
                    (
                        gid,
                        game_date,
                        g.get("home_team", ""),
                        int(g.get("home_score", 0) or 0),
                        g.get("away_team", ""),
                        int(g.get("away_score", 0) or 0),
                        g.get("home_city", ""),
                        float(g.get("home_win_prob") or 0),
                        float(g.get("away_win_prob") or 0),
                    ),
                )
                # Full stats: only read when user clicks game card
                cur.execute(
                    """
                    INSERT INTO past_game_stats (
                        past_game_id, status,
                        home_team, home_city, home_abbreviation, home_wins, home_losses, home_score,
                        home_q1, home_q2, home_q3, home_q4,
                        home_leader_pts_name, home_leader_pts_val, home_leader_reb_name, home_leader_reb_val,
                        home_leader_ast_name, home_leader_ast_val,
                        home_reb, home_ast, home_fgm, home_fga, home_ftm, home_fta, home_points, home_3pa, home_3pm,
                        away_team, away_city, away_abbreviation, away_wins, away_losses, away_score,
                        away_q1, away_q2, away_q3, away_q4,
                        away_leader_pts_name, away_leader_pts_val, away_leader_reb_name, away_leader_reb_val,
                        away_leader_ast_name, away_leader_ast_val,
                        away_reb, away_ast, away_fgm, away_fga, away_ftm, away_fta, away_points, away_3pa, away_3pm,
                        home_l10_wins, away_l10_wins
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (past_game_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        home_team = EXCLUDED.home_team, home_city = EXCLUDED.home_city,
                        home_abbreviation = EXCLUDED.home_abbreviation, home_wins = EXCLUDED.home_wins,
                        home_losses = EXCLUDED.home_losses, home_score = EXCLUDED.home_score,
                        home_q1 = EXCLUDED.home_q1, home_q2 = EXCLUDED.home_q2, home_q3 = EXCLUDED.home_q3, home_q4 = EXCLUDED.home_q4,
                        home_leader_pts_name = EXCLUDED.home_leader_pts_name, home_leader_pts_val = EXCLUDED.home_leader_pts_val,
                        home_leader_reb_name = EXCLUDED.home_leader_reb_name, home_leader_reb_val = EXCLUDED.home_leader_reb_val,
                        home_leader_ast_name = EXCLUDED.home_leader_ast_name, home_leader_ast_val = EXCLUDED.home_leader_ast_val,
                        home_reb = EXCLUDED.home_reb, home_ast = EXCLUDED.home_ast, home_fgm = EXCLUDED.home_fgm, home_fga = EXCLUDED.home_fga,
                        home_ftm = EXCLUDED.home_ftm, home_fta = EXCLUDED.home_fta, home_points = EXCLUDED.home_points,
                        home_3pa = EXCLUDED.home_3pa, home_3pm = EXCLUDED.home_3pm,
                        away_team = EXCLUDED.away_team, away_city = EXCLUDED.away_city,
                        away_abbreviation = EXCLUDED.away_abbreviation, away_wins = EXCLUDED.away_wins,
                        away_losses = EXCLUDED.away_losses, away_score = EXCLUDED.away_score,
                        away_q1 = EXCLUDED.away_q1, away_q2 = EXCLUDED.away_q2, away_q3 = EXCLUDED.away_q3, away_q4 = EXCLUDED.away_q4,
                        away_leader_pts_name = EXCLUDED.away_leader_pts_name, away_leader_pts_val = EXCLUDED.away_leader_pts_val,
                        away_leader_reb_name = EXCLUDED.away_leader_reb_name, away_leader_reb_val = EXCLUDED.away_leader_reb_val,
                        away_leader_ast_name = EXCLUDED.away_leader_ast_name, away_leader_ast_val = EXCLUDED.away_leader_ast_val,
                        away_reb = EXCLUDED.away_reb, away_ast = EXCLUDED.away_ast, away_fgm = EXCLUDED.away_fgm, away_fga = EXCLUDED.away_fga,
                        away_ftm = EXCLUDED.away_ftm, away_fta = EXCLUDED.away_fta, away_points = EXCLUDED.away_points,
                        away_3pa = EXCLUDED.away_3pa, away_3pm = EXCLUDED.away_3pm,
                        home_l10_wins = EXCLUDED.home_l10_wins, away_l10_wins = EXCLUDED.away_l10_wins
                    """,
                    (
                        gid,
                        _str(g.get("status")),
                        _str(g.get("home_team")), _str(g.get("home_city")), _str(g.get("home_abbreviation")),
                        _int(g.get("home_wins")), _int(g.get("home_losses")), int(g.get("home_score") or 0),
                        _float(g.get("home_q1")), _float(g.get("home_q2")), _float(g.get("home_q3")), _float(g.get("home_q4")),
                        _str(g.get("home_leader_pts_name")), _str(g.get("home_leader_pts_val")),
                        _str(g.get("home_leader_reb_name")), _str(g.get("home_leader_reb_val")),
                        _str(g.get("home_leader_ast_name")), _str(g.get("home_leader_ast_val")),
                        _str(g.get("home_reb")), _str(g.get("home_ast")), _str(g.get("home_fgm")), _str(g.get("home_fga")),
                        _str(g.get("home_ftm")), _str(g.get("home_fta")), _str(g.get("home_points")), _str(g.get("home_3pa")), _str(g.get("home_3pm")),
                        _str(g.get("away_team")), _str(g.get("away_city")), _str(g.get("away_abbreviation")),
                        _int(g.get("away_wins")), _int(g.get("away_losses")), int(g.get("away_score") or 0),
                        _float(g.get("away_q1")), _float(g.get("away_q2")), _float(g.get("away_q3")), _float(g.get("away_q4")),
                        _str(g.get("away_leader_pts_name")), _str(g.get("away_leader_pts_val")),
                        _str(g.get("away_leader_reb_name")), _str(g.get("away_leader_reb_val")),
                        _str(g.get("away_leader_ast_name")), _str(g.get("away_leader_ast_val")),
                        _str(g.get("away_reb")), _str(g.get("away_ast")), _str(g.get("away_fgm")), _str(g.get("away_fga")),
                        _str(g.get("away_ftm")), _str(g.get("away_fta")), _str(g.get("away_points")), _str(g.get("away_3pa")), _str(g.get("away_3pm")),
                        _int(g.get("home_l10_wins")), _int(g.get("away_l10_wins")),
                    ),
                )
                upserted += 1
    return upserted


async def save_completed_games_to_db(games_with_probs: list[dict]) -> int:
    """
    Async wrapper: persists finished games into past_game_info (for cards) and
    past_game_stats (full stats; only read when user clicks a game).

    Safe to call every 5 s — only final games are written and upserts are idempotent.

    Args:
        games_with_probs: full merged list from merge_gp() (needed for past_game_stats).

    Returns:
        Number of games saved (0 if none final yet).
    """
    import asyncio

    try:
        count = await asyncio.to_thread(_save_completed_games_sync, games_with_probs)
        if count:
            print(f"[db] saved {count} completed game(s) to past_game_info + past_game_stats")
        return count
    except psycopg2.OperationalError as e:
        print(f"[db] connection error while saving games: {e}")
        return 0
    except Exception as e:
        print(f"[db] failed to save completed games: {e}")
        return 0

def get_historical_team_stats(game_id: str) -> dict:
    """
    Fetch full stats for a past game from past_game_stats (only used when user clicks a game card).
    Returns a single game dict in the same shape as the live game detail API, or {} if not found.
    """
    try:
        gid = int(game_id)
    except (TypeError, ValueError):
        return {}
    row = execute_query(
        """
        SELECT i.past_game_id, i.game_date, i.home_team AS info_home_team, i.home_team_score,
               i.away_team AS info_away_team, i.away_team_score, i.home_win_probability, i.away_win_probability,
               s.status, s.home_team, s.home_city, s.home_abbreviation, s.home_wins, s.home_losses, s.home_score,
               s.home_q1, s.home_q2, s.home_q3, s.home_q4,
               s.home_leader_pts_name, s.home_leader_pts_val, s.home_leader_reb_name, s.home_leader_reb_val,
               s.home_leader_ast_name, s.home_leader_ast_val,
               s.home_reb, s.home_ast, s.home_fgm, s.home_fga, s.home_ftm, s.home_fta, s.home_points, s.home_3pa, s.home_3pm,
               s.away_team, s.away_city, s.away_abbreviation, s.away_wins, s.away_losses, s.away_score,
               s.away_q1, s.away_q2, s.away_q3, s.away_q4,
               s.away_leader_pts_name, s.away_leader_pts_val, s.away_leader_reb_name, s.away_leader_reb_val,
               s.away_leader_ast_name, s.away_leader_ast_val,
               s.away_reb, s.away_ast, s.away_fgm, s.away_fga, s.away_ftm, s.away_fta, s.away_points, s.away_3pa, s.away_3pm,
               s.home_l10_wins, s.away_l10_wins
        FROM past_game_info i
        JOIN past_game_stats s ON i.past_game_id = s.past_game_id
        WHERE i.past_game_id = %s
        """,
        (gid,),
        fetch_one=True,
    )
    if not row:
        return {}
    # Build response to match live game detail shape (game_id string, home_win_prob/away_win_prob from info)
    return {
        "game_id": str(row["past_game_id"]),
        "game_date": str(row["game_date"]) if row.get("game_date") else None,
        "status": row.get("status") or "Final",
        "home_team": row.get("home_team") or row.get("info_home_team") or "",
        "home_city": row.get("home_city") or "",
        "home_abbreviation": row.get("home_abbreviation") or "",
        "home_wins": row.get("home_wins"),
        "home_losses": row.get("home_losses"),
        "home_score": row.get("home_score") or row.get("home_team_score"),
        "home_q1": row.get("home_q1"), "home_q2": row.get("home_q2"), "home_q3": row.get("home_q3"), "home_q4": row.get("home_q4"),
        "home_leader_pts_name": row.get("home_leader_pts_name"), "home_leader_pts_val": row.get("home_leader_pts_val"),
        "home_leader_reb_name": row.get("home_leader_reb_name"), "home_leader_reb_val": row.get("home_leader_reb_val"),
        "home_leader_ast_name": row.get("home_leader_ast_name"), "home_leader_ast_val": row.get("home_leader_ast_val"),
        "home_reb": row.get("home_reb"), "home_ast": row.get("home_ast"),
        "home_fgm": row.get("home_fgm"), "home_fga": row.get("home_fga"),
        "home_ftm": row.get("home_ftm"), "home_fta": row.get("home_fta"),
        "home_points": row.get("home_points"), "home_3pa": row.get("home_3pa"), "home_3pm": row.get("home_3pm"),
        "away_team": row.get("away_team") or row.get("info_away_team") or "",
        "away_city": row.get("away_city") or "",
        "away_abbreviation": row.get("away_abbreviation") or "",
        "away_wins": row.get("away_wins"), "away_losses": row.get("away_losses"),
        "away_score": row.get("away_score") or row.get("away_team_score"),
        "away_q1": row.get("away_q1"), "away_q2": row.get("away_q2"), "away_q3": row.get("away_q3"), "away_q4": row.get("away_q4"),
        "away_leader_pts_name": row.get("away_leader_pts_name"), "away_leader_pts_val": row.get("away_leader_pts_val"),
        "away_leader_reb_name": row.get("away_leader_reb_name"), "away_leader_reb_val": row.get("away_leader_reb_val"),
        "away_leader_ast_name": row.get("away_leader_ast_name"), "away_leader_ast_val": row.get("away_leader_ast_val"),
        "away_reb": row.get("away_reb"), "away_ast": row.get("away_ast"),
        "away_fgm": row.get("away_fgm"), "away_fga": row.get("away_fga"),
        "away_ftm": row.get("away_ftm"), "away_fta": row.get("away_fta"),
        "away_points": row.get("away_points"), "away_3pa": row.get("away_3pa"), "away_3pm": row.get("away_3pm"),
        "home_l10_wins": row.get("home_l10_wins"), "away_l10_wins": row.get("away_l10_wins"),
        "home_win_prob": float(row["home_win_probability"]) if row.get("home_win_probability") is not None else None,
        "away_win_prob": float(row["away_win_probability"]) if row.get("away_win_probability") is not None else None,
    }


def _save_probability_history_sync(game_id: str, history: list[dict]) -> int:
    """
    Bulk-insert probability history snapshots for a completed game
    into game_probability_history.  Existing rows for the same game_id
    are deleted first so re-saves are idempotent.
    """
    if not history:
        return 0

    gid = int(game_id)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM game_probability_history WHERE game_id = %s",
                (gid,),
            )
            for snap in history:
                cur.execute(
                    """
                    INSERT INTO game_probability_history
                        (game_id, clock_display, home_team_score, away_team_score,
                         home_win_probability, away_win_probability)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        gid,
                        str(snap.get("clock", "")),
                        int(snap.get("home_score", 0) or 0),
                        int(snap.get("away_score", 0) or 0),
                        float(snap.get("home_win_prob", 0)),
                        float(snap.get("away_win_prob", 0)),
                    ),
                )
    return len(history)


async def save_probability_history(game_id: str, history: list[dict]) -> int:
    """Async wrapper: persist probability history for a finished game."""
    import asyncio
    try:
        count = await asyncio.to_thread(_save_probability_history_sync, game_id, history)
        if count:
            print(f"[db] saved {count} probability snapshots for game {game_id}")
        return count
    except Exception as e:
        print(f"[db] failed to save probability history for game {game_id}: {e}")
        return 0


def _snapshot_signature(snap: dict) -> tuple[str, int, int, float, float]:
    return (
        str(snap.get("clock", "")),
        int(snap.get("home_score", 0) or 0),
        int(snap.get("away_score", 0) or 0),
        float(snap.get("home_win_prob", 0)),
        float(snap.get("away_win_prob", 0)),
    )


def _append_probability_history_sync(game_id: str, snapshots: list[dict]) -> int:
    """
    Append new probability snapshots for a game without deleting existing rows.
    Uses latest-row signature matching for duplicate-tail protection.
    """
    if not snapshots:
        return 0

    try:
        gid = int(game_id)
    except (TypeError, ValueError):
        return 0

    inserted = 0
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT clock_display, home_team_score, away_team_score,
                       home_win_probability, away_win_probability
                FROM game_probability_history
                WHERE game_id = %s
                ORDER BY probability_id DESC
                LIMIT 1
                """,
                (gid,),
            )
            last_row = cur.fetchone()
            last_sig = None
            if last_row:
                last_sig = (
                    str(last_row["clock_display"]),
                    int(last_row["home_team_score"]),
                    int(last_row["away_team_score"]),
                    float(last_row["home_win_probability"]),
                    float(last_row["away_win_probability"]),
                )

            for snap in snapshots:
                sig = _snapshot_signature(snap)
                if last_sig is not None and sig == last_sig:
                    continue

                cur.execute(
                    """
                    INSERT INTO game_probability_history
                        (game_id, clock_display, home_team_score, away_team_score,
                         home_win_probability, away_win_probability)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        gid,
                        sig[0],
                        sig[1],
                        sig[2],
                        sig[3],
                        sig[4],
                    ),
                )
                inserted += 1
                last_sig = sig
    return inserted


async def append_probability_history(game_id: str, snapshots: list[dict]) -> int:
    """Async wrapper: append new probability snapshots for a game."""
    import asyncio

    try:
        count = await asyncio.to_thread(
            _append_probability_history_sync,
            game_id,
            snapshots,
        )
        if count:
            print(f"[db] appended {count} probability snapshots for game {game_id}")
        return count
    except Exception as e:
        print(f"[db] failed to append probability history for game {game_id}: {e}")
        return 0


def get_probability_history(game_id: str) -> list[dict]:
    """
    Fetch stored probability history for a past game from the database.
    Returns a list of snapshot dicts matching the in-memory format.
    """
    try:
        gid = int(game_id)
    except (TypeError, ValueError):
        return []

    rows = execute_query(
        """
        SELECT clock_display, home_team_score, away_team_score,
               home_win_probability, away_win_probability
        FROM game_probability_history
        WHERE game_id = %s
        ORDER BY probability_id ASC
        """,
        (gid,),
    )
    return [
        {
            "clock": row["clock_display"],
            "home_score": row["home_team_score"],
            "away_score": row["away_team_score"],
            "home_win_prob": row["home_win_probability"],
            "away_win_prob": row["away_win_probability"],
        }
        for row in rows
    ]


if __name__ == "__main__":
    test_connection()
