from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import re
from typing import Any

import requests

from util import fetch_espn_lineups

from .features import build_player_feature_context, build_stat_features
from .model_runner import predict_remaining
from .season_stats import (
    current_nba_season_key,
    get_player_season_features,
)
from .store import build_snapshot, empty_snapshot

_ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"
_TIMEOUT = 10


def _today_yyyymmdd() -> str:
    return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y%m%d")


def _summary_for_game(game_id: str) -> dict[str, Any]:
    resp = requests.get(_ESPN_SUMMARY_URL, params={"event": game_id}, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _extract_live_players(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for team_block in summary.get("boxscore", {}).get("players", []):
        team = team_block.get("team") or {}
        team_abbr = team.get("abbreviation") or ""

        for stat_group in team_block.get("statistics") or []:
            labels = stat_group.get("labels") or []
            if "PTS" not in labels:
                continue

            idx_minutes = labels.index("MIN") if "MIN" in labels else -1
            athletes = stat_group.get("athletes") or []
            for athlete in athletes:
                a = athlete.get("athlete") or {}
                player_id = str(a.get("id") or "")
                if not player_id:
                    continue
                stats = athlete.get("stats") or []
                minutes = stats[idx_minutes] if idx_minutes >= 0 and idx_minutes < len(stats) else "0"
                label_stats = {
                    str(labels[i]).upper(): stats[i]
                    for i in range(min(len(labels), len(stats)))
                }

                by_id[player_id] = {
                    "player_id": player_id,
                    "player_name": a.get("displayName") or "",
                    "team_abbr": team_abbr,
                    "minutes": minutes,
                    "stats": stats,
                    "label_stats": label_stats,
                }
    return by_id


def _build_opponent_map(lineups_game: dict[str, Any]) -> dict[str, str]:
    home = lineups_game.get("home_team") or {}
    away = lineups_game.get("away_team") or {}
    home_abbr = home.get("team_abbreviation") or ""
    away_abbr = away.get("team_abbreviation") or ""
    return {
        home_abbr: away_abbr,
        away_abbr: home_abbr,
    }


def _projection_row(
    game_id: str,
    player_id: str,
    player_name: str,
    team_abbr: str,
    opponent_abbr: str,
    is_starter: bool,
    projected_pts: float,
    projected_reb: float,
    projected_ast: float,
    game_status: str = "",
    features: dict[str, dict[str, float]] | None = None,
    model_outputs: dict[str, float] | None = None,
) -> dict[str, Any]:
    row = {
        "game_id": str(game_id),
        "player_id": str(player_id),
        "espn_player_id": str(player_id),
        "player_name": player_name,
        "team_abbr": team_abbr,
        "opponent_abbr": opponent_abbr,
        "is_starter": is_starter,
        "projected_pts": projected_pts,
        "projected_reb": projected_reb,
        "projected_ast": projected_ast,
        "game_status": game_status,
        "source": "model",
    }
    if features is not None:
        row["features"] = features
    if model_outputs is not None:
        row["model_outputs"] = model_outputs
    return row


def _to_implied_final(current_value: float, remaining_value: float) -> float:
    return round(max(0.0, float(current_value) + float(remaining_value)), 1)


def _build_pregame_player_stub(starter: dict[str, Any]) -> dict[str, Any]:
    # Stats indexes used by features.py:
    # REB idx=6, AST idx=7, FGA idx=9 ("FGM-FGA"), 3PA idx=12 ("3PM-3PA"), PTS idx=13
    stats = ["0"] * 14
    stats[9] = "0-0"
    stats[12] = "0-0"
    label_stats = {
        "MIN": "0",
        "PTS": "0",
        "REB": "0",
        "AST": "0",
        "FG": "0-0",
        "3PT": "0-0",
    }
    return {
        "player_id": str(starter.get("player_id") or ""),
        "player_name": starter.get("name") or "",
        "minutes": "0",
        "stats": stats,
        "label_stats": label_stats,
    }


def _classify_game_phase(status: str) -> str:
    s = (status or "").strip().lower()
    if not s:
        return "pregame"
    if "final" in s or "game over" in s or "f/ot" in s:
        return "final"
    if "pregame" in s or "scheduled" in s:
        return "pregame"
    if re.search(r"\b(am|pm)\b", s) and ("et" in s or "est" in s or "pt" in s or "ct" in s):
        return "pregame"
    return "live"


def _is_fallback_lineup_starter(starter: dict[str, Any]) -> bool:
    # Salary-based fallback starters include salary/jersey in util.fetch_salary_based_lineups.
    return "salary" in starter or "jersey" in starter


def _resolve_starter_player_id(starter: dict[str, Any]) -> str:
    return str(starter.get("espn_player_id") or starter.get("player_id") or "")


def _new_debug_stats(target_date: str, season_key: str) -> dict[str, Any]:
    return {
        "date": target_date,
        "season_key": season_key,
        "games_total": 0,
        "games_with_summary": 0,
        "games_with_live_players": 0,
        "starters_total": 0,
        "starters_with_live_stats": 0,
        "players_projected": 0,
        "fallback_used_pregame": 0,
        "fallback_used_live_or_final": 0,
        "fallback_candidates_selected": 0,
        "skips": {
            "missing_game_id": 0,
            "summary_fetch_failed": 0,
            "no_live_players": 0,
            "missing_team_or_starters": 0,
            "missing_starter_player_id": 0,
            "starter_not_in_live_boxscore": 0,
        },
        "summary_fetch_failed_game_ids": [],
    }


def compute_live_props_snapshot(game_date: str | None = None, debug: bool = False) -> dict[str, Any]:
    target_date = game_date or _today_yyyymmdd()
    season_key = current_nba_season_key()
    debug_stats = _new_debug_stats(target_date, season_key) if debug else None

    try:
        lineups = fetch_espn_lineups(target_date)
    except Exception as e:
        print(f"[live_props] lineup fetch failed: {e}")
        payload = empty_snapshot()
        if debug and debug_stats is not None:
            debug_stats["lineup_fetch_failed"] = str(e)
            payload["debug"] = debug_stats
        return payload

    games = lineups.get("games") or []
    if debug and debug_stats is not None:
        debug_stats["games_total"] = len(games)
    if not games:
        payload = empty_snapshot()
        if debug and debug_stats is not None:
            payload["debug"] = debug_stats
        return payload

    projections: list[dict[str, Any]] = []

    for game in games:
        game_id = str(game.get("game_id") or "")
        if not game_id:
            if debug and debug_stats is not None:
                debug_stats["skips"]["missing_game_id"] += 1
            continue

        try:
            summary = _summary_for_game(game_id)
        except Exception as e:
            print(f"[live_props] summary fetch failed game_id={game_id}: {e}")
            if debug and debug_stats is not None:
                debug_stats["skips"]["summary_fetch_failed"] += 1
                debug_stats["summary_fetch_failed_game_ids"].append(game_id)
            continue

        if debug and debug_stats is not None:
            debug_stats["games_with_summary"] += 1

        live_players = _extract_live_players(summary)
        no_live_players_for_game = len(live_players) == 0
        if no_live_players_for_game:
            if debug and debug_stats is not None:
                debug_stats["skips"]["no_live_players"] += 1
        else:
            if debug and debug_stats is not None:
                debug_stats["games_with_live_players"] += 1

        comp = (summary.get("header", {}).get("competitions") or [{}])[0]
        competitors = comp.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})
        game_context = {
            "status": comp.get("status", {}).get("type", {}).get("shortDetail") or "",
            "home_score": int(home.get("score", 0) or 0),
            "away_score": int(away.get("score", 0) or 0),
            "home_abbreviation": (home.get("team") or {}).get("abbreviation", ""),
            "away_abbreviation": (away.get("team") or {}).get("abbreviation", ""),
        }
        game_phase = _classify_game_phase(game_context["status"])

        opp_map = _build_opponent_map(game)

        for side in ("home_team", "away_team"):
            team = game.get(side) or {}
            team_abbr = str(team.get("team_abbreviation") or "")
            starters = team.get("starters") or []
            if not team_abbr or not starters:
                if debug and debug_stats is not None:
                    debug_stats["skips"]["missing_team_or_starters"] += 1
                continue

            team_is_fallback = any(_is_fallback_lineup_starter(s) for s in starters)
            if debug and debug_stats is not None and team_is_fallback:
                debug_stats["fallback_candidates_selected"] += len(starters)
                if game_phase == "pregame":
                    debug_stats["fallback_used_pregame"] += 1
                else:
                    debug_stats["fallback_used_live_or_final"] += 1

            opponent_abbr = opp_map.get(team_abbr, "")
            for starter in starters:
                is_starter = not _is_fallback_lineup_starter(starter)
                if debug and debug_stats is not None:
                    if is_starter:
                        debug_stats["starters_total"] += 1
                player_id = _resolve_starter_player_id(starter)
                if not player_id:
                    if debug and debug_stats is not None:
                        debug_stats["skips"]["missing_starter_player_id"] += 1
                    continue
                live = live_players.get(player_id)

                if live is None and no_live_players_for_game:
                    # Pregame stats fallback only; player selection is now lineup-driven.
                    live = _build_pregame_player_stub(
                        {"player_id": player_id, "name": starter.get("name") or ""}
                    )
                    player_game_ctx = {
                        **game_context,
                        "status": "Pregame",
                        "home_score": 0,
                        "away_score": 0,
                        "is_home": team_abbr == game_context.get("home_abbreviation"),
                    }
                elif live is None:
                    # If game has live rows but this starter is not present, skip.
                    if debug and debug_stats is not None:
                        debug_stats["skips"]["starter_not_in_live_boxscore"] += 1
                    continue
                else:
                    if debug and debug_stats is not None:
                        if is_starter:
                            debug_stats["starters_with_live_stats"] += 1

                    player_game_ctx = {
                        **game_context,
                        "is_home": team_abbr == game_context.get("home_abbreviation"),
                    }
                player_name = live.get("player_name") or starter.get("name") or ""
                season_features = get_player_season_features(
                    espn_player_id=player_id,
                    season_key=season_key,
                    player_name=player_name,
                    team_abbr=team_abbr,
                )
                base_features = build_player_feature_context(
                    live,
                    player_game_ctx,
                    season_features=season_features,
                )
                pts_features = build_stat_features("pts", base_features)
                reb_features = build_stat_features("reb", base_features)
                ast_features = build_stat_features("ast", base_features)

                pts_remaining = predict_remaining("pts", pts_features)
                reb_remaining = predict_remaining("reb", reb_features)
                ast_remaining = predict_remaining("ast", ast_features)

                pts = _to_implied_final(base_features.get("current_points", 0.0), pts_remaining)
                reb = _to_implied_final(base_features.get("current_rebounds", 0.0), reb_remaining)
                ast = _to_implied_final(base_features.get("current_assists", 0.0), ast_remaining)

                projections.append(
                    _projection_row(
                        game_id=game_id,
                        player_id=player_id,
                        player_name=player_name,
                        team_abbr=team_abbr,
                        opponent_abbr=opponent_abbr,
                        is_starter=is_starter,
                        projected_pts=pts,
                        projected_reb=reb,
                        projected_ast=ast,
                        game_status=game_context.get("status", ""),
                        features=(
                            {
                                "base": {k: float(v) for k, v in base_features.items()},
                                "pts_model": pts_features,
                                "reb_model": reb_features,
                                "ast_model": ast_features,
                            }
                            if debug
                            else None
                        ),
                        model_outputs=(
                            {
                                "pts_remaining_raw": float(pts_remaining),
                                "reb_remaining_raw": float(reb_remaining),
                                "ast_remaining_raw": float(ast_remaining),
                                "pts_implied_final": float(pts),
                                "reb_implied_final": float(reb),
                                "ast_implied_final": float(ast),
                            }
                            if debug
                            else None
                        ),
                    )
                )
                if debug and debug_stats is not None:
                    debug_stats["players_projected"] += 1

    payload = build_snapshot(projections)
    if debug and debug_stats is not None:
        payload["debug"] = debug_stats
    return payload
