"""
Scrape play-by-play for ~top 5 players per team (up to 150 players) over the last 3 seasons.
Build a dataset with the listed features to train a model that predicts a player's
total points at the end of the game from in-game state.

Features:
  seconds_remaining, current_points, current_minutes, season_ppg, season_fga, season_mpg,
  fga_so_far, 3pa_so_far, season_3pa, score_differential

Target:
  final_points (total points the player scores in the game)
"""

import os
import time
from pathlib import Path

import pandas as pd
import requests
import threading
from tqdm import tqdm
from nba_api.stats.endpoints import leaguegamefinder, leaguedashplayerstats

SEC_PER_QUARTER = 720
OT_PERIOD_SEC = 300
REGULATION_SEC = 4 * SEC_PER_QUARTER
TOP_N_PER_TEAM = 1
SEASONS = ["2022-23", "2023-24", "2024-25"]
API_DELAY = 0.600


def parse_clock_to_seconds(clock: str | None) -> int | None:
    if not clock:
        return None
    s = str(clock).strip()
    if s.startswith("PT") and "S" in s:
        s = s.replace("PT", "").replace("S", "")
        minutes = 0
        seconds = 0
        if "M" in s:
            mins, s = s.split("M", 1)
            minutes = int(mins) if mins.isdigit() else 0
        if s:
            try:
                seconds = int(float(s))
            except ValueError:
                seconds = 0
        return minutes * 60 + seconds
    if ":" in s:
        try:
            mins, secs = s.split(":", 1)
            return int(mins) * 60 + int(float(secs))
        except ValueError:
            return None
    return None


def seconds_remaining_in_game(period: int, clock_sec: int | None) -> int | None:
    if clock_sec is None or period < 1:
        return None
    if period <= 4:
        return (4 - period) * SEC_PER_QUARTER + clock_sec
    return clock_sec


def game_elapsed_seconds(period: int, clock_sec: int | None) -> int | None:
    """Seconds from game start to this (period, clock) moment."""
    if clock_sec is None or period < 1:
        return None
    if period <= 4:
        return (period - 1) * SEC_PER_QUARTER + (SEC_PER_QUARTER - clock_sec)
    return REGULATION_SEC + (period - 5) * OT_PERIOD_SEC + (OT_PERIOD_SEC - clock_sec)


def is_substitution(action: dict) -> bool:
    return (action.get("actionType") or "").lower() == "substitution"


def substitution_type(action: dict) -> str | None:
    """Return 'in' or 'out' for substitution, else None."""
    if not is_substitution(action):
        return None
    return (action.get("subType") or "").lower() or None


def get_top_players_and_season_stats(season: str) -> tuple[set[int], pd.DataFrame]:
    """Return (set of player IDs to track, DataFrame of season stats: PLAYER_ID, SEASON_PPG, SEASON_FGA, SEASON_3PA, SEASON_MPG)."""
    for attempt in range(1, 4):
        try:
            ld = leaguedashplayerstats.LeagueDashPlayerStats(season=season)
            df = ld.get_data_frames()[0]
            time.sleep(API_DELAY)
            break
        except Exception as e:
            print(f"LeagueDashPlayerStats failed (attempt {attempt}/3): {e}")
            time.sleep(API_DELAY * (2 ** attempt))
    else:
        raise RuntimeError("LeagueDashPlayerStats failed after 3 attempts.")

    team_col = "TEAM_ID"
    df = df[df["GP"].notna() & (df["GP"] > 0)]
    df["PTS"] = pd.to_numeric(df["PTS"], errors="coerce").fillna(0)
    df["FGA"] = pd.to_numeric(df["FGA"], errors="coerce").fillna(0)
    df["FG3A"] = pd.to_numeric(df["FG3A"], errors="coerce").fillna(0)
    df["GP"] = pd.to_numeric(df["GP"], errors="coerce").fillna(1)

    def parse_min(s):
        if pd.isna(s):
            return float("nan")
        s = str(s).strip()
        if ":" in s:
            parts = s.split(":", 1)
            try:
                return int(parts[0]) + int(parts[1]) / 60.0
            except (ValueError, IndexError):
                return float("nan")
        try:
            return float(s)
        except ValueError:
            return float("nan")
    min_series = pd.to_numeric(df["MIN"], errors="coerce")
    min_series = min_series.fillna(df["MIN"].map(parse_min))
    df["REB"] = pd.to_numeric(df["REB"], errors="coerce").fillna(0)
    df["AST"] = pd.to_numeric(df["AST"], errors="coerce").fillna(0)
    df["SEASON_MPG"] = min_series / df["GP"]
    df["SEASON_PPG"] = df["PTS"] / df["GP"]
    df["SEASON_FGA"] = df["FGA"] / df["GP"]
    df["SEASON_3PA"] = df["FG3A"] / df["GP"]
    df["SEASON_RPG"] = df["REB"] / df["GP"]
    df["SEASON_APG"] = df["AST"] / df["GP"]

    top_players = set()
    season_stats = []
    for _, group in df.groupby(team_col):
        top = group.nlargest(TOP_N_PER_TEAM, "PTS")
        for _, row in top.iterrows():
            pid = int(row["PLAYER_ID"])
            top_players.add(pid)
            season_stats.append({
                "PLAYER_ID": pid,
                "SEASON_PPG": float(row["SEASON_PPG"]),
                "SEASON_FGA": float(row["SEASON_FGA"]),
                "SEASON_3PA": float(row["SEASON_3PA"]),
                "SEASON_MPG": float(row["SEASON_MPG"]),
                "SEASON_RPG": float(row["SEASON_RPG"]),
                "SEASON_APG": float(row["SEASON_APG"]),
            })
    stats_df = pd.DataFrame(season_stats)
    return top_players, stats_df


def fetch_games_for_season(season: str) -> pd.DataFrame:
    time.sleep(API_DELAY)
    for attempt in range(1, 4):
        try:
            lgf = leaguegamefinder.LeagueGameFinder(
                season_nullable=season,
                season_type_nullable="Regular Season",
                league_id_nullable="00",
            )
            games = lgf.get_data_frames()[0]
            games["SEASON"] = season
            games["IS_HOME"] = games["MATCHUP"].str.contains("vs", case=False, na=False)
            home = games[games["IS_HOME"]][["GAME_ID", "TEAM_ID"]].rename(columns={"TEAM_ID": "HOME_TEAM_ID"})
            away = games[~games["IS_HOME"]][["GAME_ID", "TEAM_ID"]].rename(columns={"TEAM_ID": "AWAY_TEAM_ID"})
            merged = home.merge(away, on="GAME_ID").drop_duplicates("GAME_ID")
            merged["SEASON"] = season
            time.sleep(API_DELAY)
            return merged
        except Exception as e:
            print(f"LeagueGameFinder failed (attempt {attempt}/3): {e}")
            time.sleep(API_DELAY * (2 ** attempt))
    raise RuntimeError("LeagueGameFinder failed after 3 attempts.")


def fetch_playbyplay(game_id: str) -> list[dict]:
    url = f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game_id}.json"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    return data.get("game", {}).get("actions", [])


def is_scoring_attempt(action: dict) -> bool:
    at = (action.get("actionType") or "").lower()
    return at in ("2pt", "3pt", "freethrow")


def points_on_play(action: dict) -> int:
    """Points scored on this single play (1–3). Do not use pointsTotal from API; it is the player's running game total."""
    if action.get("shotResult") != "Made":
        return 0
    at = (action.get("actionType") or "").lower()
    if at == "2pt":
        return 2
    if at == "3pt":
        return 3
    if at == "freethrow":
        return 1
    return 0


def is_three_attempt(action: dict) -> bool:
    return (action.get("actionType") or "").lower() == "3pt"


def is_fga(action: dict) -> bool:
    at = (action.get("actionType") or "").lower()
    return at in ("2pt", "3pt")


def is_rebound(action: dict) -> bool:
    return (action.get("actionType") or "").lower() == "rebound"


def get_assist_person_id(action: dict) -> int | None:
    """Return personId of the assister if this action has an assist, else None."""
    aid = action.get("assistPersonId")
    if aid is not None and aid != 0:
        return int(aid)
    return None


def build_game_rows(
    game_id: str,
    season: str,
    actions: list[dict],
    tracked_players: set[int],
    season_stats: pd.DataFrame,
    home_team_id: int,
    away_team_id: int,
) -> list[dict]:
    """
    First pass: compute final points/rebounds/assists per player.
    Second pass: at each play where a tracked player scores, gets a rebound, or gets an assist, emit a row (state after the play).
    """
    final_points: dict[int, int] = {}
    player_points: dict[int, int] = {}
    player_fga: dict[int, int] = {}
    player_3pa: dict[int, int] = {}
    player_rebounds: dict[int, int] = {}
    player_assists: dict[int, int] = {}
    stats_by_player = season_stats.set_index("PLAYER_ID").to_dict("index") if not season_stats.empty else {}

    def get_season_ppg(pid: int) -> float:
        return stats_by_player.get(pid, {}).get("SEASON_PPG", 0.0)

    def get_season_fga(pid: int) -> float:
        return stats_by_player.get(pid, {}).get("SEASON_FGA", 0.0)

    def get_season_3pa(pid: int) -> float:
        return stats_by_player.get(pid, {}).get("SEASON_3PA", 0.0)

    def get_season_mpg(pid: int) -> float:
        return stats_by_player.get(pid, {}).get("SEASON_MPG", 0.0)

    def get_season_rebounds(pid: int) -> float:
        return stats_by_player.get(pid, {}).get("SEASON_RPG", 0.0)

    def get_season_assists(pid: int) -> float:
        return stats_by_player.get(pid, {}).get("SEASON_APG", 0.0)

    # First pass: accumulate points, FGA, 3PA, rebounds, assists per player
    for action in actions:
        pid = action.get("personId") or 0
        if pid != 0:
            pts = points_on_play(action)
            if pts > 0:
                player_points[pid] = player_points.get(pid, 0) + pts
            if is_fga(action):
                player_fga[pid] = player_fga.get(pid, 0) + 1
            if is_three_attempt(action):
                player_3pa[pid] = player_3pa.get(pid, 0) + 1
            if is_rebound(action):
                player_rebounds[pid] = player_rebounds.get(pid, 0) + 1
        aid = get_assist_person_id(action)
        if aid is not None:
            player_assists[aid] = player_assists.get(aid, 0) + 1

    # Include players who scored, got a rebound, or had an assist
    players_with_stats = (
        set(player_points.keys())
        | set(player_rebounds.keys())
        | set(player_assists.keys())
    )
    tracked_with_points = tracked_players & players_with_stats
    if not tracked_with_points:
        return []

    final_points = {p: player_points.get(p, 0) for p in tracked_with_points}
    final_rebounds = {p: player_rebounds.get(p, 0) for p in tracked_with_points}
    final_assists = {p: player_assists.get(p, 0) for p in tracked_with_points}

    rows = []
    player_points = {p: 0 for p in tracked_with_points}
    player_fga_cur = {p: 0 for p in tracked_with_points}
    player_3pa_cur = {p: 0 for p in tracked_with_points}
    player_rebounds_cur = {p: 0 for p in tracked_with_points}
    player_assists_cur = {p: 0 for p in tracked_with_points}
    # Player minutes: how many minutes each tracked player has played so far
    player_minutes_played: dict[int, float] = {p: 0.0 for p in tracked_with_points}
    player_stint_start_sec: dict[int, float | None] = {p: None for p in tracked_with_points}
    home_score = 0
    away_score = 0

    def period_start_game_sec(p: int) -> float:
        if p <= 4:
            return (p - 1) * SEC_PER_QUARTER
        return REGULATION_SEC + (p - 5) * OT_PERIOD_SEC

    for action in actions:
        period = int(action.get("period") or 1)
        clock_sec = parse_clock_to_seconds(action.get("clock"))
        sec_rem = seconds_remaining_in_game(period, clock_sec)
        game_sec = game_elapsed_seconds(period, clock_sec)
        if sec_rem is None or game_sec is None:
            continue
        score_h = action.get("scoreHome")
        score_a = action.get("scoreAway")
        if score_h is not None and score_a is not None:
            try:
                home_score = int(score_h)
                away_score = int(score_a)
            except (TypeError, ValueError):
                pass
        score_diff = home_score - away_score

        pid = action.get("personId") or 0

        # Process substitutions to track player minutes played
        sub_type = substitution_type(action)
        if sub_type == "out" and pid in tracked_with_points:
            start = player_stint_start_sec.get(pid)
            if start is not None:
                player_minutes_played[pid] = player_minutes_played.get(pid, 0) + (game_sec - start) / 60.0
            player_stint_start_sec[pid] = None
        elif sub_type == "in" and pid in tracked_with_points:
            player_stint_start_sec[pid] = float(game_sec)
        # Update rebounds/assists for any tracked player on this action (before we possibly continue)
        if is_rebound(action) and pid in tracked_with_points:
            player_rebounds_cur[pid] = player_rebounds_cur.get(pid, 0) + 1
        aid = get_assist_person_id(action)
        if aid is not None and aid in tracked_with_points:
            player_assists_cur[aid] = player_assists_cur.get(aid, 0) + 1

        # Collect all tracked players to emit for this action: scorer, rebounder, assister
        pts = points_on_play(action)
        players_to_emit: set[int] = set()
        if pid in tracked_with_points and (is_rebound(action) or pts > 0):
            players_to_emit.add(pid)
        if aid is not None and aid in tracked_with_points:
            players_to_emit.add(aid)
        if not players_to_emit:
            continue

        # Starter backdate for any player we'll emit
        for p in players_to_emit:
            if player_stint_start_sec.get(p) is None and not is_substitution(action):
                player_stint_start_sec[p] = period_start_game_sec(period)

        if pid in tracked_with_points and is_fga(action):
            player_fga_cur[pid] = player_fga_cur.get(pid, 0) + 1
        if pid in tracked_with_points and is_three_attempt(action):
            player_3pa_cur[pid] = player_3pa_cur.get(pid, 0) + 1
        if pts > 0:
            player_points[pid] = player_points.get(pid, 0) + pts

        for p in players_to_emit:
            stint_start = player_stint_start_sec.get(p)
            if stint_start is not None:
                current_minutes = player_minutes_played.get(p, 0) + (game_sec - stint_start) / 60.0
            else:
                current_minutes = player_minutes_played.get(p, 0)

            rows.append({
                "game_id": game_id,
                "player_id": p,
                "season": season,
                "seconds_remaining": sec_rem,
                "current_points": player_points.get(p, 0),
                "current_minutes": round(current_minutes, 2),
                "season_ppg": round(get_season_ppg(p), 2),
                "season_fga": round(get_season_fga(p), 2),
                "season_mpg": round(get_season_mpg(p), 2),
                "fga_so_far": player_fga_cur.get(p, 0),
                "3pa_so_far": player_3pa_cur.get(p, 0),
                "season_3pa": round(get_season_3pa(p), 2),
                "current_rebounds": player_rebounds_cur.get(p, 0),
                "season_rebounds": round(get_season_rebounds(p), 2),
                "current_assists": player_assists_cur.get(p, 0),
                "season_assists": round(get_season_assists(p), 2),
                "score_differential": score_diff,
                "final_points": final_points[p],
                "final_rebounds": final_rebounds[p],
                "final_assists": final_assists[p],
            })

    return rows

lock = threading.Lock()
all_rows = []
def scrape_season(season: str):
    print("Fetching season stats for", season)
    try:
        tracked, season_stats_df = get_top_players_and_season_stats(season)
        print(f"Tracking {len(tracked)} players (top {TOP_N_PER_TEAM} per team).")
    except Exception as e:
        print(f"Skipping season {season}: {e}")
        return

    games_df = fetch_games_for_season(season)
    games_list = games_df.to_dict("records")
    for row in tqdm(games_list, desc=f"PBP {season}", unit="game"):
        game_id = str(row["GAME_ID"])
        home_id = int(row["HOME_TEAM_ID"])
        away_id = int(row["AWAY_TEAM_ID"])
        try:
            actions = fetch_playbyplay(game_id)
        except Exception as e:
            tqdm.write(f"Skip {game_id}: {e}")
            time.sleep(API_DELAY)
            continue
        game_rows = build_game_rows(
            game_id=game_id,
            season=season,
            actions=actions,
            tracked_players=tracked,
            season_stats=season_stats_df,
            home_team_id=home_id,
            away_team_id=away_id,
        )
        global all_rows
        with lock:
            all_rows.extend(game_rows)
        time.sleep(API_DELAY)


def main():
    all_rows.clear()

    out_dir = Path(__file__).resolve().parent.parent / "datasets"
    out_dir.mkdir(parents=True, exist_ok=True)
    output_csv = out_dir / "props_training.csv"

    threads = []
    for season in SEASONS:
        thread = threading.Thread(target=scrape_season, args=(season,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    if all_rows:
        df = pd.DataFrame(all_rows)
        df = df.sort_values(["season", "game_id", "player_id", "seconds_remaining"], ascending=[True, True, True, False])
        df.to_csv(output_csv, index=False)
        print(f"\nSaved {len(df)} rows to {output_csv}")
    else:
        print("No rows generated.")


if __name__ == "__main__":
    main()
