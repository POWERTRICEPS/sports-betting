from __future__ import annotations

import re
from datetime import UTC, datetime, date
from typing import Any

import requests
from nba_api.stats.endpoints import leaguedashplayerstats

SeasonFeatureSet = dict[str, float]

_ESPN_SPLITS_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/athletes/{athlete_id}/splits"
_ESPN_GAMELOG_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/athletes/{athlete_id}/gamelog"
_ESPN_CORE_STATS_URL = "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/athletes/{athlete_id}/statistics"
_ESPN_COMMON_V3_STATS_URL = "https://site.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{athlete_id}/stats"
_TIMEOUT = 8

_cache_date: date | None = None
_season_feature_cache: dict[tuple[str, str], SeasonFeatureSet] = {}
_espn_to_nba_id_cache: dict[str, int] = {}
_nba_season_tables: dict[str, dict[str, Any]] = {}


def zero_feature_set() -> SeasonFeatureSet:
    return {
        "season_ppg": 0.0,
        "season_fga": 0.0,
        "season_mpg": 0.0,
        "season_3pa": 0.0,
        "season_rebounds": 0.0,
        "season_assists": 0.0,
    }


def _is_missing_feature_value(value: float) -> bool:
    return float(value) <= 0.0


def _merge_feature_sets(primary: SeasonFeatureSet, fallback: SeasonFeatureSet) -> SeasonFeatureSet:
    merged: SeasonFeatureSet = {}
    keys = [
        "season_ppg",
        "season_fga",
        "season_mpg",
        "season_3pa",
        "season_rebounds",
        "season_assists",
    ]
    for key in keys:
        p = float(primary.get(key, 0.0) or 0.0)
        f = float(fallback.get(key, 0.0) or 0.0)
        merged[key] = f if _is_missing_feature_value(p) and f > 0.0 else p
    return merged


def current_nba_season_key(now: datetime | None = None) -> str:
    ts = now or datetime.now(UTC)
    year = ts.year
    if ts.month >= 10:
        return f"{year}-{str(year + 1)[-2:]}"
    return f"{year - 1}-{str(year)[-2:]}"


def _ensure_daily_cache() -> None:
    global _cache_date
    today = datetime.now(UTC).date()
    if _cache_date == today:
        return

    _season_feature_cache.clear()
    _espn_to_nba_id_cache.clear()
    _nba_season_tables.clear()
    _cache_date = today


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if not s:
        return None
    s = s.replace("%", "")
    if s.startswith("."):
        s = f"0{s}"
    if re.fullmatch(r"-?\d+(?:\.\d+)?", s):
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _season_key_to_espn_year(season_key: str) -> int | None:
    try:
        suffix = season_key.split("-")[1]
        return int(f"20{suffix}")
    except Exception:
        return None


def _parse_attempts_from_made_attempted(token: Any) -> float | None:
    if token is None:
        return None
    s = str(token).strip()
    if "-" not in s:
        return _safe_float(s)
    parts = s.split("-", 1)
    return _safe_float(parts[1])


def _parse_espn_common_v3_payload(payload: dict[str, Any], season_key: str) -> SeasonFeatureSet | None:
    categories = payload.get("categories") or []
    averages = next((c for c in categories if str(c.get("name", "")).lower() == "averages"), None)
    if not isinstance(averages, dict):
        return None

    labels = [str(x).strip().upper() for x in (averages.get("labels") or [])]
    rows = averages.get("statistics") or []
    if not labels or not rows:
        return None

    target_year = _season_key_to_espn_year(season_key)
    selected_row: dict[str, Any] | None = None
    if target_year is not None:
        for row in rows:
            year = ((row.get("season") or {}).get("year"))
            try:
                if int(year) == target_year:
                    selected_row = row
                    break
            except Exception:
                continue
    if selected_row is None and rows:
        selected_row = rows[-1]
    if not isinstance(selected_row, dict):
        return None

    stats = selected_row.get("stats") or []
    if not isinstance(stats, list):
        return None

    def _value(label: str) -> Any:
        if label not in labels:
            return None
        idx = labels.index(label)
        if idx < 0 or idx >= len(stats):
            return None
        return stats[idx]

    mpg = _safe_float(_value("MIN"))
    ppg = _safe_float(_value("PTS"))
    rpg = _safe_float(_value("REB"))
    apg = _safe_float(_value("AST"))
    fga = _parse_attempts_from_made_attempted(_value("FG"))
    three_pa = _parse_attempts_from_made_attempted(_value("3PT"))

    if any(v is not None for v in [ppg, fga, mpg, three_pa, rpg, apg]):
        return {
            "season_ppg": float(ppg or 0.0),
            "season_fga": float(fga or 0.0),
            "season_mpg": float(mpg or 0.0),
            "season_3pa": float(three_pa or 0.0),
            "season_rebounds": float(rpg or 0.0),
            "season_assists": float(apg or 0.0),
        }
    return None


def _extract_stat_pairs(node: Any, out: dict[str, float]) -> None:
    if isinstance(node, list):
        for item in node:
            _extract_stat_pairs(item, out)
        return

    if not isinstance(node, dict):
        return

    key_raw = node.get("name") or node.get("abbreviation") or node.get("shortName")
    value = _safe_float(node.get("value"))
    if value is None:
        value = _safe_float(node.get("displayValue"))

    if key_raw and value is not None:
        out[str(key_raw).strip().lower()] = value

    for v in node.values():
        if isinstance(v, (dict, list)):
            _extract_stat_pairs(v, out)


def _pick_stat(flat: dict[str, float], keys: list[str], lo: float, hi: float) -> float | None:
    for k in keys:
        if k not in flat:
            continue
        v = flat[k]
        if lo <= v <= hi:
            return v
    return None


def _parse_espn_payload(payload: dict[str, Any]) -> SeasonFeatureSet | None:
    flat: dict[str, float] = {}
    _extract_stat_pairs(payload, flat)

    # ESPN core stats commonly exposes per-game fields as avg* keys.
    ppg = _pick_stat(flat, ["avgpoints", "ppg", "pointspergame", "pts", "points"], 0.0, 60.0)
    fga = _pick_stat(
        flat,
        ["avgfieldgoalsattempted", "avgfga", "fgapergame", "fieldgoalsattemptedpergame", "fga"],
        0.0,
        40.0,
    )
    mpg = _pick_stat(flat, ["avgminutes", "minutespergame", "mpg", "min"], 0.0, 48.0)
    three_pa = _pick_stat(
        flat,
        ["avgthreepointfieldgoalsattempted", "avg3pa", "threepointattemptspergame", "threepointfieldgoalsattemptedpergame", "3pa", "fg3a"],
        0.0,
        20.0,
    )
    rpg = _pick_stat(flat, ["avgrebounds", "rpg", "reboundspergame", "rebounds", "reb"], 0.0, 25.0)
    apg = _pick_stat(flat, ["avgassists", "apg", "assistspergame", "assists", "ast"], 0.0, 20.0)

    if any(v is not None for v in [ppg, fga, mpg, three_pa, rpg, apg]):
        return {
            "season_ppg": float(ppg or 0.0),
            "season_fga": float(fga or 0.0),
            "season_mpg": float(mpg or 0.0),
            "season_3pa": float(three_pa or 0.0),
            "season_rebounds": float(rpg or 0.0),
            "season_assists": float(apg or 0.0),
        }
    return None


def _fetch_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        resp = requests.get(url, params=params, timeout=_TIMEOUT)
        if resp.status_code >= 400:
            return None
        return resp.json()
    except Exception:
        return None


def _fetch_espn_season_features(espn_player_id: str, season_key: str) -> SeasonFeatureSet | None:
    common_v3_payload = _fetch_json(
        _ESPN_COMMON_V3_STATS_URL.format(athlete_id=espn_player_id),
        {"seasontype": "2"},
    )
    if common_v3_payload:
        parsed_common_v3 = _parse_espn_common_v3_payload(common_v3_payload, season_key)
        if parsed_common_v3 is not None:
            return parsed_common_v3

    season_start_year = season_key.split("-")[0]

    urls = [
        (_ESPN_SPLITS_URL.format(athlete_id=espn_player_id), {"season": season_start_year}),
        (_ESPN_GAMELOG_URL.format(athlete_id=espn_player_id), {"season": season_start_year}),
        (_ESPN_CORE_STATS_URL.format(athlete_id=espn_player_id), {"lang": "en", "region": "us"}),
    ]

    for url, params in urls:
        payload = _fetch_json(url, params)
        if not payload:
            continue
        parsed = _parse_espn_payload(payload)
        if parsed is not None:
            return parsed

    return None


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", name.lower())).strip()


def _load_nba_season_table(season_key: str) -> dict[str, Any]:
    if season_key in _nba_season_tables:
        return _nba_season_tables[season_key]

    try:
        dash = leaguedashplayerstats.LeagueDashPlayerStats(season=season_key)
        df = dash.get_data_frames()[0]
    except Exception as e:
        print(f"[season_stats] LeagueDashPlayerStats failed for {season_key}: {e}")
        table = {"by_id": {}, "by_name_team": {}}
        _nba_season_tables[season_key] = table
        return table

    by_id: dict[int, SeasonFeatureSet] = {}
    by_name_team: dict[tuple[str, str], int] = {}
    by_team_top_mpg: dict[str, list[dict[str, Any]]] = {}

    for _, row in df.iterrows():
        try:
            player_id = int(row.get("PLAYER_ID"))
        except Exception:
            continue

        gp = float(row.get("GP") or 0.0)
        mpg = _safe_float(row.get("MIN"))
        if mpg is None:
            mpg = 0.0
        if gp > 0 and mpg > 48:
            mpg = mpg / gp

        features = {
            "season_ppg": float((_safe_float(row.get("PTS")) or 0.0) / gp) if gp > 0 else 0.0,
            "season_fga": float((_safe_float(row.get("FGA")) or 0.0) / gp) if gp > 0 else 0.0,
            "season_mpg": float(mpg or 0.0),
            "season_3pa": float((_safe_float(row.get("FG3A")) or 0.0) / gp) if gp > 0 else 0.0,
            "season_rebounds": float((_safe_float(row.get("REB")) or 0.0) / gp) if gp > 0 else 0.0,
            "season_assists": float((_safe_float(row.get("AST")) or 0.0) / gp) if gp > 0 else 0.0,
        }
        by_id[player_id] = features

        name = str(row.get("PLAYER_NAME") or "")
        team = str(row.get("TEAM_ABBREVIATION") or "").upper()
        if name and team:
            by_name_team[(_normalize_name(name), team)] = player_id
            by_team_top_mpg.setdefault(team, []).append(
                {
                    "player_id": player_id,
                    "player_name": name,
                    "team_abbr": team,
                    "season_mpg": float(mpg or 0.0),
                }
            )

    for team_abbr, players in by_team_top_mpg.items():
        players.sort(key=lambda p: float(p.get("season_mpg", 0.0)), reverse=True)
        by_team_top_mpg[team_abbr] = players

    table = {
        "by_id": by_id,
        "by_name_team": by_name_team,
        "by_team_top_mpg": by_team_top_mpg,
    }
    _nba_season_tables[season_key] = table
    return table


def get_team_top_mpg_players(season_key: str, team_abbr: str, limit: int = 5) -> list[dict[str, Any]]:
    _ensure_daily_cache()
    table = _load_nba_season_table(season_key)
    team_key = str(team_abbr or "").upper()
    players = list(table.get("by_team_top_mpg", {}).get(team_key, []))
    return players[: max(0, int(limit))]


def register_player_identity(
    espn_player_id: str,
    player_name: str,
    team_abbr: str,
    season_key: str,
) -> int | None:
    _ensure_daily_cache()

    if espn_player_id in _espn_to_nba_id_cache:
        return _espn_to_nba_id_cache[espn_player_id]

    table = _load_nba_season_table(season_key)
    lookup_key = (_normalize_name(player_name), str(team_abbr or "").upper())
    nba_player_id = table.get("by_name_team", {}).get(lookup_key)
    if nba_player_id is None:
        return None

    _espn_to_nba_id_cache[espn_player_id] = int(nba_player_id)
    return int(nba_player_id)


def _get_nba_fallback_features(espn_player_id: str, season_key: str) -> SeasonFeatureSet | None:
    nba_player_id = _espn_to_nba_id_cache.get(espn_player_id)
    if nba_player_id is None:
        return None

    table = _load_nba_season_table(season_key)
    return table.get("by_id", {}).get(nba_player_id)


def get_player_season_features(
    espn_player_id: str,
    season_key: str,
    player_name: str | None = None,
    team_abbr: str | None = None,
) -> SeasonFeatureSet:
    _ensure_daily_cache()

    cache_key = (season_key, espn_player_id)
    cached = _season_feature_cache.get(cache_key)
    if cached is not None:
        # Heal partially-resolved cache rows by attempting NBA backfill.
        if any(_is_missing_feature_value(cached.get(k, 0.0)) for k in zero_feature_set().keys()):
            if player_name and team_abbr:
                register_player_identity(espn_player_id, player_name, team_abbr, season_key)
            nba_features = _get_nba_fallback_features(espn_player_id, season_key)
            if nba_features is not None:
                merged = _merge_feature_sets(cached, nba_features)
                _season_feature_cache[cache_key] = merged
                return merged
        return cached

    espn_features = _fetch_espn_season_features(espn_player_id, season_key)
    if player_name and team_abbr:
        register_player_identity(espn_player_id, player_name, team_abbr, season_key)

    nba_features = _get_nba_fallback_features(espn_player_id, season_key)
    if espn_features is not None and nba_features is not None:
        merged = _merge_feature_sets(espn_features, nba_features)
        _season_feature_cache[cache_key] = merged
        return merged
    if espn_features is not None:
        _season_feature_cache[cache_key] = espn_features
        return espn_features
    if nba_features is not None:
        _season_feature_cache[cache_key] = nba_features
        return nba_features

    zeros = zero_feature_set()
    _season_feature_cache[cache_key] = zeros
    return zeros
