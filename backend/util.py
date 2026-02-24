"""
Computes win probabilities for each game based on the teams' records and the home team's record.
Uses a trained logistic regression model (ml/model.joblib) when available for in-progress games.

Structured output:
{
    "game_id": {
        "home_win_prob": 0.6,
        "away_win_prob": 0.4
    }
}
"""
import os
import re
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests

from nba_api.stats.endpoints import leaguestandings

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

# NBA stats API TeamID -> ESPN-style abbreviation (for matching scoreboard teams)
_NBA_TEAM_ID_TO_ABBREV = {
    1610612737: "ATL", 1610612738: "BOS", 1610612751: "BKN", 1610612766: "CHA",
    1610612741: "CHI", 1610612739: "CLE", 1610612742: "DAL", 1610612743: "DEN",
    1610612765: "DET", 1610612744: "GSW", 1610612745: "HOU", 1610612754: "IND",
    1610612746: "LAC", 1610612747: "LAL", 1610612763: "MEM", 1610612748: "MIA",
    1610612749: "MIL", 1610612750: "MIN", 1610612740: "NOP", 1610612752: "NYK",
    1610612760: "OKC", 1610612753: "ORL", 1610612755: "PHI", 1610612756: "PHX",
    1610612757: "POR", 1610612758: "SAC", 1610612759: "SAS", 1610612761: "TOR",
    1610612762: "UTA", 1610612764: "WAS",
}

_ESPN_STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/basketball/nba/standings"
_ESPN_STANDINGS_TIMEOUT = 10
_ESPN_STANDINGS_RETRIES = 3
_STANDINGS_CACHE: list[dict[str, Any]] | None = None
_STANDINGS_CACHE_AT: datetime | None = None
import pandas as pd

_ML_MODEL_PATH = Path(__file__).resolve().parent / "pred_models" / "lr.joblib"
_wp_model = None
_wp_model_load_attempted = False

def _load_wp_model():
    """Load the win-probability model once; returns None when unavailable or unloadable."""
    global _wp_model, _wp_model_load_attempted
    if _wp_model is not None:
        return _wp_model
    if _wp_model_load_attempted:
        return None
    _wp_model_load_attempted = True
    if not _ML_MODEL_PATH.is_file():
        print(f"WP model not found at {_ML_MODEL_PATH}; using fallback probabilities.")
        return None
    try:
        import joblib
        _wp_model = joblib.load(_ML_MODEL_PATH)
        return _wp_model
    except Exception as e:
        print(f"WP model load failed ({_ML_MODEL_PATH}): {e}. Using fallback probabilities.")
        return None

_SEC_PER_QUARTER = 720
_SEC_TOTAL_REGULATION = 2880
_SEC_OT = 300

def parse_status(status: str) -> tuple[int | None, int | None]:
    """
    Extract (period, seconds_remaining) from status string.
    Format: "{clock} - {period}" e.g. "40.2 - 4th", "1:23 - 4th", "7:07 - 3rd"
    Period: 1-4 for quarters, 5=OT, 6=2OT, etc. Seconds: remaining in entire game.
    """
    if not status or "Final" in status:
        return 4, 0
    if "Pregame" in status or "Scheduled" in status:
        return 1, _SEC_TOTAL_REGULATION
    if "Halftime" in status:
        return 2, _SEC_TOTAL_REGULATION // 2  # 1440
    if "Overtime" in status:
        return 5, _SEC_OT
    if "End of 1st" in status:
        return 2, _SEC_PER_QUARTER * 3
    if "End of 2nd" in status:
        return 3, _SEC_PER_QUARTER * 2
    if "End of 3rd" in status:
        return 4, _SEC_PER_QUARTER
    if "End of 4th" in status:
        return 4, 0

    match = re.match(r"(.+?)\s*-\s*(.+)", status.strip())
    if not match:
        return None, None

    clock_str, period_str = match.group(1).strip(), match.group(2).strip()

    # if game hasn't started yet, return period and seconds remaining for full game
    if re.search(r"\d{1,2}:\d{2}\s*(AM|PM)?", period_str, re.I):
        return 1, _SEC_TOTAL_REGULATION

    period_str_lower = period_str.lower()
    if period_str_lower in ("1st", "1"):
        period = 1
    elif period_str_lower in ("2nd", "2"):
        period = 2
    elif period_str_lower in ("3rd", "3"):
        period = 3
    elif period_str_lower in ("4th", "4"):
        period = 4
    else:
        ot_match = re.match(r"(\d*)ot", period_str_lower)
        if ot_match:
            period = 4 + int(ot_match.group(1) or 1)
        else:
            return None, None

    if ":" in clock_str:
        parts = clock_str.split(":")
        try:
            mins, secs = int(parts[0]), int(float(parts[1]) if parts[1] else 0)
            sec_left_in_q = mins * 60 + secs
        except (ValueError, IndexError):
            return None, None
    else:
        try:
            sec_left_in_q = int(float(clock_str))
        except ValueError:
            return None, None

    if period <= 4:
        full_quarters_left = 4 - period
        seconds_remaining = sec_left_in_q + full_quarters_left * _SEC_PER_QUARTER
        return period, seconds_remaining
    else:
        return period, sec_left_in_q

def calculate(
    home_score: int,
    away_score: int,
    home_wins: int,
    home_losses: int,
    away_wins: int,
    away_losses: int,
    home_l10_wins: int,
    away_l10_wins: int,
    status: str,
) -> tuple[float, float]:
    # Check if game hasn't started yet - use pregame defaults
    if "EST" in status or "ET" in status or status in ("Pregame", "Scheduled"):
        home_score = 0
        away_score = 0
        period = 1
        seconds_remaining = 48 * 60  # 48 minutes = 2880 seconds
        point_diff = 0
    elif status == "Final":
        home_win_prob = 0.0 if home_score < away_score else 100.0
        away_win_prob = 100.0 - home_win_prob
        return home_win_prob, away_win_prob

    model = _load_wp_model()
    if model is not None:
        _, seconds_remaining = parse_status(status)
        if seconds_remaining is None:
            print("Invalid status")
            return 0, 0
        FEATURE_COLS = ["SECONDS_REMAINING", "HOME_SCORE", "AWAY_SCORE", "HOME_WINS", "HOME_LOSSES", "AWAY_WINS", "AWAY_LOSSES", "HOME_L10_WINS", "AWAY_L10_WINS"]
        X = pd.DataFrame(
            [[seconds_remaining, home_score, away_score, home_wins, home_losses, away_wins, away_losses, home_l10_wins, away_l10_wins]],
            columns=FEATURE_COLS,
        )

        # for xgboost, xgboost_calibrated, random_forest, lr
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)[0]
        # neural network
        else:
            p = float(model.predict(X, verbose=0).ravel()[0])
            proba = (1 - p, p)
        home_win_prob = float(100 * proba[1])
        away_win_prob = float(100 - home_win_prob)
        return home_win_prob, away_win_prob

    print("No model found")
    return 50.0, 50.0  # Only fallback when model is completely missing

def compute_win_probabilities(games: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    result = {}
    for game in games:
        game_id = game["game_id"]
        home_score = game["home_score"]
        away_score = game["away_score"]
        status = game["status"]
        home_wins = game["home_wins"]
        home_losses = game["home_losses"]
        away_wins = game["away_wins"]
        away_losses = game["away_losses"]
        home_l10_wins = game.get("home_l10_wins", 0)
        away_l10_wins = game.get("away_l10_wins", 0)

        home_win_prob, away_win_prob = calculate(
            home_score, away_score,
            home_wins, home_losses, away_wins, away_losses,
            home_l10_wins, away_l10_wins,
            status,
        )
        result[game_id] = {
            "home_win_prob": float(home_win_prob),
            "away_win_prob": float(away_win_prob),
        }
    return result


def _get_stat(stats: list, name: str) -> str | None:
    """Get displayValue for a stat by name."""
    for s in stats or []:
        if s.get("name") == name:
            return s.get("displayValue")
    return None


def _get_leader(leaders: list, stat: str) -> tuple[str | None, str | None]:
    """Get (name, value) for points/rebounds/assists leader. Value is displayValue string."""
    for entry in leaders or []:
        if entry.get("name") == stat and entry.get("leaders"):
            leader = entry["leaders"][0]
            name = leader.get("athlete", {}).get("fullName")
            val = leader.get("displayValue")
            return name, val
    return None, None


def _quarters_from_linescores(linescores: list) -> tuple[Any, Any, Any, Any]:
    """Extract Q1-Q4 from linescores. Returns (q1, q2, q3, q4) with 0 for missing."""
    by_period = {p.get("period"): p.get("value") for p in (linescores or []) if p.get("period") <= 4}
    return (
        by_period.get(1),
        by_period.get(2),
        by_period.get(3),
        by_period.get(4),
    )


def parse_game_data(event: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse game data from ESPN scoreboard API event.
    Returns dictionary with team names, scores, points per quarter, status, team leaders, abbreviations, records.
    """
    comps = event.get("competitions") or []
    if not comps:
        return None
    comp = comps[0]
    competitors = comp.get("competitors") or []
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home or not away:
        return None

    status_obj = comp.get("status") or {}
    status = status_obj.get("type", {}).get("shortDetail") or status_obj.get("type", {}).get("description") or ""

    def _parse_records(records: list) -> tuple[int, int]:
        rec = next((r for r in (records or []) if r.get("name") == "overall" or r.get("type") == "total"), None)
        summary = (rec or {}).get("summary", "") or ""
        parts = summary.split("-")
        if len(parts) != 2:
            return 0, 0
        try:
            return int(parts[0].strip()), int(parts[1].strip())
        except ValueError:
            return 0, 0

    def _team(c: dict) -> dict:
        t = c.get("team") or {}
        stats_list = c.get("statistics") or c.get("stats") or []
        leaders = c.get("leaders") or []
        wins, losses = _parse_records(c.get("records"))
        pts_name, pts_val = _get_leader(leaders, "points")
        reb_name, reb_val = _get_leader(leaders, "rebounds")
        ast_name, ast_val = _get_leader(leaders, "assists")
        q1, q2, q3, q4 = _quarters_from_linescores(c.get("linescores"))
        return {
            "team_name": t.get("shortDisplayName") or t.get("name", ""),
            "city": t.get("location", ""),
            "abbreviation": t.get("abbreviation", ""),
            "wins": wins,
            "losses": losses,
            "score": int(c.get("score", 0) or 0),
            "q1": q1, "q2": q2, "q3": q3, "q4": q4,
            "reb": _get_stat(stats_list, "rebounds"),
            "ast": _get_stat(stats_list, "assists"),
            "fga": _get_stat(stats_list, "fieldGoalsAttempted"),
            "fgm": _get_stat(stats_list, "fieldGoalsMade"),
            "fta": _get_stat(stats_list, "freeThrowsAttempted"),
            "ftm": _get_stat(stats_list, "freeThrowsMade"),
            "points": _get_stat(stats_list, "points"),
            "three_pa": _get_stat(stats_list, "threePointFieldGoalsAttempted"),
            "three_pm": _get_stat(stats_list, "threePointFieldGoalsMade"),
            "leader_pts_name": pts_name, "leader_pts_val": pts_val,
            "leader_reb_name": reb_name, "leader_reb_val": reb_val,
            "leader_ast_name": ast_name, "leader_ast_val": ast_val,
        }

    h, a = _team(home), _team(away)

    def _team_slice(team: dict, prefix: str) -> dict:
        return {
            f"{prefix}_team": team["team_name"],
            f"{prefix}_city": team["city"],
            f"{prefix}_abbreviation": team["abbreviation"],
            f"{prefix}_wins": team["wins"],
            f"{prefix}_losses": team["losses"],
            f"{prefix}_score": team["score"],
            f"{prefix}_q1": team["q1"], f"{prefix}_q2": team["q2"],
            f"{prefix}_q3": team["q3"], f"{prefix}_q4": team["q4"],
            f"{prefix}_leader_pts_name": team["leader_pts_name"],
            f"{prefix}_leader_pts_val": team["leader_pts_val"],
            f"{prefix}_leader_reb_name": team["leader_reb_name"],
            f"{prefix}_leader_reb_val": team["leader_reb_val"],
            f"{prefix}_leader_ast_name": team["leader_ast_name"],
            f"{prefix}_leader_ast_val": team["leader_ast_val"],
            f"{prefix}_reb": team.get("reb"),
            f"{prefix}_ast": team.get("ast"),
            f"{prefix}_fga": team.get("fga"),
            f"{prefix}_fgm": team.get("fgm"),
            f"{prefix}_fta": team.get("fta"),
            f"{prefix}_ftm": team.get("ftm"),
            f"{prefix}_points": team.get("points"),
            f"{prefix}_3pa": team.get("three_pa"),
            f"{prefix}_3pm": team.get("three_pm"),
        }

    return {
        "game_id": event.get("id", ""),
        "status": status,
        **_team_slice(h, "home"),
        **_team_slice(a, "away"),
    }

def merge_gp(g: list[dict[str, Any]], p: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    """
    Appends home_win_prob and away_win_prob to each game in the list.
    """
    result = []
    for game in g:
        game_id = game["game_id"]
        row = {**game, "home_win_prob": None, "away_win_prob": None}
        if game_id in p:
            row["home_win_prob"] = p[game_id]["home_win_prob"]
            row["away_win_prob"] = p[game_id]["away_win_prob"]
        result.append(row)
    return result


def parse_dashboard_game_data(event: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse lightweight game data for dashboard display.
    Returns only: game_id, status, team names, abbreviations, records, scores.
    This is a minimal subset compared to parse_game_data().
    """
    comps = event.get("competitions") or []
    if not comps:
        return None
    comp = comps[0]
    competitors = comp.get("competitors") or []
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home or not away:
        return None

    status_obj = comp.get("status") or {}
    status = status_obj.get("type", {}).get("shortDetail") or status_obj.get("type", {}).get("description") or ""

    def _parse_records(records: list) -> tuple[int, int]:
        rec = next((r for r in (records or []) if r.get("name") == "overall" or r.get("type") == "total"), None)
        summary = (rec or {}).get("summary", "") or ""
        parts = summary.split("-")
        if len(parts) != 2:
            return 0, 0
        try:
            return int(parts[0].strip()), int(parts[1].strip())
        except ValueError:
            return 0, 0

    def _team_dashboard(c: dict) -> dict:
        t = c.get("team") or {}
        wins, losses = _parse_records(c.get("records"))
        return {
            "team_name": t.get("shortDisplayName") or t.get("name", ""),
            "city": t.get("location", ""),
            "abbreviation": t.get("abbreviation", ""),
            "wins": wins,
            "losses": losses,
            "score": int(c.get("score", 0) or 0),
        }

    h, a = _team_dashboard(home), _team_dashboard(away)

    return {
        "game_id": event.get("id", ""),
        "status": status,
        "home_team": h["team_name"],
        "home_city": h["city"],
        "home_abbreviation": h["abbreviation"],
        "home_wins": h["wins"],
        "home_losses": h["losses"],
        "home_score": h["score"],
        "away_team": a["team_name"],
        "away_city": a["city"],
        "away_abbreviation": a["abbreviation"],
        "away_wins": a["wins"],
        "away_losses": a["losses"],
        "away_score": a["score"],
    }

def parse_lineup_data(raw_data: dict, game_date: str) -> dict:
    """
    Parse raw NBA lineup data into structured format.
    
    Args:
        raw_data: Raw JSON from NBA stats endpoint
        game_date: Date string (YYYYMMDD)
    
    Returns:
        Structured lineup data matching acceptance criteria
    """
    games = []
    
    # Extract teams data from raw response
    # NBA's structure may vary, so we handle multiple possible formats
    teams_data = raw_data.get("teams", []) or raw_data.get("resultSets", [])
    
    if isinstance(teams_data, list) and len(teams_data) > 0:
        # Group teams by game
        games_dict = {}
        
        for team_data in teams_data:
            # Extract team information
            team_info = {
                "team_name": team_data.get("team_name") or team_data.get("teamName") or "",
                "team_abbreviation": team_data.get("team_abbreviation") or team_data.get("teamTricode") or team_data.get("abbr") or "",
                "starters": []
            }
            
            # Extract starters (usually 5 players)
            starters_data = team_data.get("starters", []) or team_data.get("players", [])
            
            for player in starters_data[:5]:  # Ensure only 5 starters
                starter = {
                    "name": player.get("player_name") or player.get("playerName") or player.get("name") or "Unknown",
                    "position": player.get("position") or player.get("pos") or "",
                    "player_id": str(player.get("player_id") or player.get("playerId") or player.get("id") or "")
                }
                team_info["starters"].append(starter)
            
            # Try to extract game_id and group by matchup
            game_id = team_data.get("game_id") or team_data.get("gameId") or ""
            
            if game_id:
                if game_id not in games_dict:
                    games_dict[game_id] = {
                        "game_id": game_id,
                        "home_team": None,
                        "away_team": None
                    }
                
                # Determine if home or away (based on indicator in data)
                is_home = team_data.get("home_away") == "home" or team_data.get("isHome") == True
                
                if is_home:
                    games_dict[game_id]["home_team"] = team_info
                else:
                    games_dict[game_id]["away_team"] = team_info
        
        # Convert dict to list and filter out incomplete games
        games = [
            game for game in games_dict.values() 
            if game["home_team"] and game["away_team"]
        ]
    
    # Check for confirmed lineups status
    lineup_status = raw_data.get("LINEUP_STATUS") or raw_data.get("lineupStatus") or "unknown"
    confirmed = lineup_status.lower() == "confirmed" if isinstance(lineup_status, str) else False
    
    return {
        "date": game_date,
        "lineup_status": "confirmed" if confirmed else "projected",
        "games": games,
        "total_games": len(games)
    }

def get_player_props(player_name: str) -> dict[str, Any]:
    """
    Get player props from The Odds API. 
    Retrieves points, rebounds, and assist O/U lines for a given player for different betting platforms. 
    https://api.sportsgameodds.com/v2/events?apiKey=API_KEY_HERE&leagueID=NBA&oddsAvailable=true&oddIDs=points-PLAYER_ID-game-ou-over,points-PLAYER_ID-game-ou-under
    """
    player_entity_id = "_".join(player_name.split(" ")).upper() + "_1_NBA"

    def get_stat_odds(stat: str) -> dict[str, Any]:
        if stat == "points":
            url = f"https://api.sportsgameodds.com/v2/events?apiKey={ODDS_API_KEY}&leagueID=NBA&oddsAvailable=true&oddIDs=points-{player_entity_id}-game-ou-over,points-{player_entity_id}-game-ou-under"
        elif stat == "rebounds":
            url = f"https://api.sportsgameodds.com/v2/events?apiKey={ODDS_API_KEY}&leagueID=NBA&oddsAvailable=true&oddIDs=rebounds-{player_entity_id}-game-ou-over,rebounds-{player_entity_id}-game-ou-under"
        elif stat == "assists":
            url = f"https://api.sportsgameodds.com/v2/events?apiKey={ODDS_API_KEY}&leagueID=NBA&oddsAvailable=true&oddIDs=assists-{player_entity_id}-game-ou-over,assists-{player_entity_id}-game-ou-under"
        else:
            raise ValueError(f"Invalid stat: {stat}")
        response = requests.get(url)
        data = response.json()
        return data["data"][0]["odds"]

    payload = {}
    for stat in ["points", "rebounds", "assists"]:
        data = get_stat_odds(stat)
        # rebounds-JALEN_DUREN_1_NBA-game-ou-over
        over_key = f"{stat}-{player_entity_id}-game-ou-over"
        under_key = f"{stat}-{player_entity_id}-game-ou-under"

        def get_prop_odds(prop_json: dict) -> dict[str, Any]:
            ret = {}
            for bookmaker, odds in prop_json.items():
                ret[bookmaker] = {
                    "odds": odds["odds"],
                    "line": odds["overUnder"],
                }
            return ret

        over_prop_odds = get_prop_odds(data[over_key]["byBookmaker"])
        under_prop_odds = get_prop_odds(data[under_key]["byBookmaker"])

        payload[stat] = {
            "over": over_prop_odds,
            "under": under_prop_odds,
        }

    return payload


# --- Standings and games helpers (used by main.py routes) ---

def _parse_l10(l10_str: str) -> tuple[int, int]:
    """Parse L10 string like '7-3' or '4-6' into (wins, losses). Returns (0, 0) on failure."""
    if not l10_str or "-" not in l10_str:
        return 0, 0
    parts = l10_str.strip().split("-")
    if len(parts) != 2:
        return 0, 0
    try:
        return int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        return 0, 0


def _current_nba_season() -> str:
    """e.g. Oct 2025 -> '2025-26'; July 2025 -> '2025-26'."""
    today = date.today()
    year = today.year
    if today.month >= 10:
        return f"{year}-{str(year + 1)[-2:]}"
    return f"{year - 1}-{str(year)[-2:]}"


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _format_streak(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    if " " in s:
        return s
    if len(s) >= 2 and s[0] in ("W", "L") and s[1:].isdigit():
        return f"{s[0]} {s[1:]}"
    return s


def _normalize_espn_entries(entries: list[dict[str, Any]], conference: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, entry in enumerate(entries, start=1):
        team = entry.get("team") or {}
        stats = entry.get("stats") or []
        stats_map: dict[str, Any] = {}
        for stat in stats:
            key = stat.get("name") or stat.get("abbreviation")
            if not key:
                continue
            stats_map[key] = stat.get("displayValue") if stat.get("displayValue") is not None else stat.get("value")

        wins = _to_int(stats_map.get("wins"))
        losses = _to_int(stats_map.get("losses"))
        rank = _to_int(stats_map.get("playoffSeed"), default=idx)

        out.append(
            {
                "team_id": _to_int(team.get("id")),
                "team_city": team.get("location") or team.get("name") or "",
                "team_name": team.get("name") or team.get("displayName") or "",
                "conference": conference,
                "rank": rank,
                "record": stats_map.get("summary") or f"{wins}-{losses}",
                "win_pct": _to_float(stats_map.get("winPercent")),
                "team_L10": stats_map.get("Last Ten Games") or "",
                "curr_streak": _format_streak(str(stats_map.get("streak") or "")),
            }
        )
    out.sort(key=lambda team: team.get("rank", 999))
    return out


def fetch_standings_from_espn() -> list[dict[str, Any]]:
    """
    Fetch league standings from ESPN. Returns [{"east_standings": [...], "west_standings": [...]}].
    Uses cache on upstream failure. Raises Exception on final failure (caller may map to HTTPException).
    """
    global _STANDINGS_CACHE, _STANDINGS_CACHE_AT

    last_error: Exception | None = None
    for attempt in range(1, _ESPN_STANDINGS_RETRIES + 1):
        try:
            resp = requests.get(_ESPN_STANDINGS_URL, timeout=_ESPN_STANDINGS_TIMEOUT)
            resp.raise_for_status()
            raw = resp.json()

            east: list[dict[str, Any]] = []
            west: list[dict[str, Any]] = []

            for child in raw.get("children") or []:
                conf_name = (child.get("abbreviation") or child.get("name") or "").lower()
                standings_block = child.get("standings") or {}
                entries = standings_block.get("entries") or child.get("entries") or []
                if "east" in conf_name:
                    east = _normalize_espn_entries(entries, "East")
                elif "west" in conf_name:
                    west = _normalize_espn_entries(entries, "West")

            if not east and not west:
                raise ValueError("ESPN standings payload missing east/west entries")

            result = [{"east_standings": east, "west_standings": west}]
            _STANDINGS_CACHE = result
            _STANDINGS_CACHE_AT = datetime.utcnow()
            return result
        except Exception as e:
            last_error = e
            print(f"ESPN standings fetch failed (attempt {attempt}/{_ESPN_STANDINGS_RETRIES}): {e}")
            if attempt < _ESPN_STANDINGS_RETRIES:
                time.sleep(attempt)

    if _STANDINGS_CACHE is not None:
        cache_age = "unknown"
        if _STANDINGS_CACHE_AT is not None:
            cache_age = f"{int((datetime.utcnow() - _STANDINGS_CACHE_AT).total_seconds())}s"
        print(f"Serving cached standings after upstream failure (cache age: {cache_age}).")
        return _STANDINGS_CACHE

    raise Exception(f"Failed to fetch standings from ESPN: {last_error}")


def _l10_by_abbrev_from_espn_standings() -> dict[str, tuple[int, int]]:
    """
    Build mapping abbreviation -> (l10_wins, l10_losses) from fetch_standings_from_espn().
    Uses team_id from standings + _NBA_TEAM_ID_TO_ABBREV (ESPN uses same team IDs as NBA).
    """
    abbrev_to_l10: dict[str, tuple[int, int]] = {}
    data = fetch_standings_from_espn()
    block = data[0] if data else {}
    east = block.get("east_standings") or []
    west = block.get("west_standings") or []
    for entry in east + west:
        team_id = entry.get("team_id")
        l10_str = (entry.get("team_L10") or "").strip()
        w, l = _parse_l10(l10_str)
        abbrev = _NBA_TEAM_ID_TO_ABBREV.get(team_id)
        if abbrev:
            abbrev_to_l10[abbrev] = (w, l)
    if "UTA" in abbrev_to_l10:
        abbrev_to_l10["UTAH"] = abbrev_to_l10["UTA"]
    return abbrev_to_l10


def fetch_games_from_nba() -> list[dict[str, Any]]:
    """
    Fetch full game data from ESPN API with all stats.
    Used by /api/games/stats endpoint for detailed statistics.
    """
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    raw = resp.json()
    events = raw.get("events", [])
    result = []
    l10_by_abbrev = _l10_by_abbrev_from_espn_standings()
    for event in events:
        payload = parse_game_data(event)
        if payload:
            home_abbrev = payload.get("home_abbreviation", "") or ""
            away_abbrev = payload.get("away_abbreviation", "") or ""
            h_w, h_l = l10_by_abbrev.get(home_abbrev, (0, 0))
            a_w, a_l = l10_by_abbrev.get(away_abbrev, (0, 0))
            payload["home_l10_wins"] = h_w
            payload["away_l10_wins"] = a_w
            result.append(payload)
    return result


def fetch_dashboard_games() -> list[dict[str, Any]]:
    """
    Fetch lightweight game data from ESPN API for dashboard display.
    Returns only: game_id, status, team names/abbr, records, scores.
    Used by /api/games endpoint.
    """
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    raw = resp.json()
    events = raw.get("events", [])
    result = []
    for event in events:
        payload = parse_dashboard_game_data(event)
        if payload:
            result.append(payload)
    return result
