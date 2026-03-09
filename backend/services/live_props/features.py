from __future__ import annotations

import re
from typing import Any

from util import parse_status


def _parse_float_token(token: str) -> float:
    try:
        return float(token)
    except (TypeError, ValueError):
        return 0.0


def parse_minutes(minutes_str: str | None) -> float:
    if not minutes_str:
        return 0.0

    s = minutes_str.strip()
    if ":" in s:
        parts = s.split(":")
        if len(parts) >= 2:
            mins = _parse_float_token(parts[0])
            secs = _parse_float_token(parts[1])
            return mins + (secs / 60.0)

    match = re.match(r"^(\d+)(?:\.\d+)?$", s)
    if match:
        return _parse_float_token(match.group(1))

    return 0.0


def _extract_stat(stats: list[str], idx: int) -> float:
    if idx < 0 or idx >= len(stats):
        return 0.0
    token = str(stats[idx]).strip()
    if not token:
        return 0.0

    # Handles values like "5-12" for FGM-FGA and "2-7" for 3PM-3PA.
    if "-" in token:
        parts = token.split("-")
        if len(parts) == 2:
            return _parse_float_token(parts[1])

    return _parse_float_token(token)


def _extract_by_label(label_stats: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        token = label_stats.get(key.upper())
        if token is not None:
            return str(token)
    return None


def _extract_attempts_from_token(token: str | None) -> float:
    if token is None:
        return 0.0
    s = str(token).strip()
    if not s:
        return 0.0
    if "-" in s:
        parts = s.split("-")
        if len(parts) == 2:
            return _parse_float_token(parts[1])
    return _parse_float_token(s)


def build_player_feature_context(
    player: dict[str, Any],
    game: dict[str, Any],
    season_features: dict[str, float] | None = None,
) -> dict[str, float]:
    status = str(game.get("status") or "")
    _, seconds_remaining = parse_status(status)

    stats = player.get("stats") or []
    label_stats = {
        str(k).upper(): v for k, v in (player.get("label_stats") or {}).items()
    }

    pts_token = _extract_by_label(label_stats, ["PTS", "POINTS"])
    reb_token = _extract_by_label(label_stats, ["REB", "REBOUNDS"])
    ast_token = _extract_by_label(label_stats, ["AST", "ASSISTS"])
    fg_token = _extract_by_label(label_stats, ["FG", "FGM-FGA", "FIELD GOALS"])
    three_pt_token = _extract_by_label(label_stats, ["3PT", "3PM-3PA", "3P"])
    min_token = _extract_by_label(label_stats, ["MIN", "MINUTES"])

    current_points = _parse_float_token(pts_token) if pts_token is not None else _extract_stat(stats, 13)
    current_rebounds = _parse_float_token(reb_token) if reb_token is not None else _extract_stat(stats, 6)
    current_assists = _parse_float_token(ast_token) if ast_token is not None else _extract_stat(stats, 7)
    fga_so_far = _extract_attempts_from_token(fg_token) if fg_token is not None else _extract_stat(stats, 9)
    three_pa_so_far = _extract_attempts_from_token(three_pt_token) if three_pt_token is not None else _extract_stat(stats, 12)

    minutes_raw = min_token if min_token is not None else player.get("minutes")
    current_minutes = parse_minutes(str(minutes_raw) if minutes_raw is not None else None)

    home_score = float(game.get("home_score") or 0.0)
    away_score = float(game.get("away_score") or 0.0)
    is_home = bool(game.get("is_home"))
    score_differential = (home_score - away_score) if is_home else (away_score - home_score)

    season = season_features or {}
    season_mpg = float(season.get("season_mpg", 0.0) or 0.0)
    season_ppg = float(season.get("season_ppg", 0.0) or 0.0)
    season_fga = float(season.get("season_fga", 0.0) or 0.0)
    season_3pa = float(season.get("season_3pa", 0.0) or 0.0)
    season_rebounds = float(season.get("season_rebounds", 0.0) or 0.0)
    season_assists = float(season.get("season_assists", 0.0) or 0.0)

    return {
        "seconds_remaining": float(seconds_remaining or 0.0),
        "current_points": current_points,
        "current_rebounds": current_rebounds,
        "current_assists": current_assists,
        "current_minutes": current_minutes,
        "fga_so_far": fga_so_far,
        "3pa_so_far": three_pa_so_far,
        "score_differential": float(score_differential),
        "season_mpg": season_mpg,
        "season_ppg": season_ppg,
        "season_fga": season_fga,
        "season_3pa": season_3pa,
        "season_rebounds": season_rebounds,
        "season_assists": season_assists,
    }


def build_stat_features(stat: str, base_features: dict[str, float]) -> dict[str, float]:
    if stat == "pts":
        keys = [
            "seconds_remaining",
            "current_points",
            "current_minutes",
            "season_ppg",
            "season_fga",
            "season_mpg",
            "fga_so_far",
            "3pa_so_far",
            "season_3pa",
            "score_differential",
        ]
    elif stat == "reb":
        keys = [
            "seconds_remaining",
            "current_minutes",
            "season_mpg",
            "current_rebounds",
            "season_rebounds",
            "score_differential",
        ]
    else:
        keys = [
            "seconds_remaining",
            "current_minutes",
            "season_mpg",
            "current_assists",
            "season_assists",
            "score_differential",
        ]

    return {k: float(base_features.get(k, 0.0) or 0.0) for k in keys}
