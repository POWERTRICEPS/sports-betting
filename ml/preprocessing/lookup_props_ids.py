#!/usr/bin/env python3
"""
Look up what game and player correspond to a game_id and player_id from props_training.csv.

Usage:
  python lookup_props_ids.py <game_id> <player_id>
  python lookup_props_ids.py 0022201219 1630532

  Or look up a random row from the training CSV:
  python lookup_props_ids.py --sample
  python lookup_props_ids.py --sample --csv ml/datasets/props_training.csv

Requires: nba_api, pandas (pip install nba_api pandas)
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import boxscoresummaryv2, commonplayerinfo, leaguegamefinder


def get_player_info(player_id: int) -> dict | None:
    """Get player name and basic info from NBA API."""
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=str(player_id))
        df = info.common_player_info.get_data_frame()
        if df.empty:
            return None
        row = df.iloc[0]
        return {
            "id": player_id,
            "name": row.get("DISPLAY_FIRST_LAST", "Unknown"),
            "team": row.get("TEAM_ABBREVIATION", ""),
            "position": row.get("POSITION", ""),
        }
    except Exception as e:
        return {"id": player_id, "name": "Unknown", "error": str(e)}


def _game_id_to_season(game_id: str) -> str:
    """Infer season from game_id (e.g. 0022201219 -> 2022-23)."""
    if len(game_id) >= 5:
        yy = game_id[3:5]  # 22, 23, 24...
        return f"20{yy}-{int(yy)+1:02d}"
    return "2023-24"


def get_game_info(game_id: str) -> dict | None:
    """Get game details (teams, date, score) from NBA API."""
    # Try boxscoresummaryv2 first (has game summary + line score)
    try:
        summary = boxscoresummaryv2.BoxScoreSummaryV2(game_id=game_id)
        game_summary = getattr(summary, "game_summary", None)
        line_score = getattr(summary, "line_score", None)
        if game_summary is None or line_score is None:
            dfs = summary.get_data_frames()
            game_summary = dfs[0] if len(dfs) > 0 else pd.DataFrame()
            line_score = dfs[1] if len(dfs) > 1 else pd.DataFrame()
        else:
            game_summary = game_summary.get_data_frame()
            line_score = line_score.get_data_frame()
        if not game_summary.empty:
            row = game_summary.iloc[0]
            teams = []
            if not line_score.empty:
                for _, ls in line_score.iterrows():
                    teams.append({
                        "team": str(ls.get("TEAM_ABBREVIATION", "")),
                        "pts": int(ls.get("PTS", 0)),
                    })
            return {
                "game_id": game_id,
                "date": str(row.get("GAME_DATE_EST", "")),
                "matchup": str(row.get("GAME_STATUS_TEXT", "")),
                "teams": teams,
            }
    except Exception:
        pass
    # Fallback: LeagueGameFinder filtered by game_id
    try:
        season = _game_id_to_season(game_id)
        lgf = leaguegamefinder.LeagueGameFinder(
            season_nullable=season,
            season_type_nullable="Regular Season",
            league_id_nullable="00",
        )
        games = lgf.get_data_frames()[0]
        match = games[games["GAME_ID"].astype(str) == str(game_id)]
        if not match.empty:
            row = match.iloc[0]
            return {
                "game_id": game_id,
                "date": str(row.get("GAME_DATE", "")),
                "matchup": str(row.get("MATCHUP", "")),
                "teams": [],
            }
    except Exception as e:
        return {"game_id": game_id, "error": str(e)}
    return {"game_id": game_id, "error": "Game not found"}


def main():
    parser = argparse.ArgumentParser(
        description="Look up game and player for IDs from props_training.csv"
    )
    parser.add_argument(
        "game_id",
        nargs="?",
        help="10-digit game ID (e.g. 0022201219)",
    )
    parser.add_argument(
        "player_id",
        nargs="?",
        type=int,
        help="Player ID (e.g. 1630532)",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Pick a random row from props_training.csv to look up",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Path to props CSV (default: ml/datasets/props_training.csv)",
    )
    args = parser.parse_args()

    if args.sample:
        csv_path = args.csv
        if csv_path is None:
            script_dir = Path(__file__).resolve().parent
            csv_path = script_dir.parent / "datasets" / "props_training.csv"
        csv_path = Path(csv_path)
        if not csv_path.exists():
            print(f"CSV not found: {csv_path}", file=sys.stderr)
            sys.exit(1)
        df = pd.read_csv(csv_path, nrows=100000)  # sample from first 100k rows
        if df.empty:
            print("CSV is empty", file=sys.stderr)
            sys.exit(1)
        row = df.sample(n=1).iloc[0]
        game_id = str(row["game_id"])
        player_id = int(row["player_id"])
        print(f"Random sample from {csv_path.name}: game_id={game_id}, player_id={player_id}")
        print()
    elif args.game_id and args.player_id:
        game_id = args.game_id
        player_id = args.player_id
    else:
        parser.print_help()
        print("\nExample: python lookup_props_ids.py 0022201219 1630532", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("PLAYER")
    print("=" * 60)
    player = get_player_info(player_id)
    if player:
        print(f"  ID:       {player['id']}")
        print(f"  Name:     {player.get('name', 'Unknown')}")
        if "team" in player and player["team"]:
            print(f"  Team:     {player['team']}")
        if "position" in player and player["position"]:
            print(f"  Position: {player['position']}")
        if "error" in player:
            print(f"  Error:    {player['error']}")
    else:
        print(f"  Player ID {player_id} not found")

    print()
    print("=" * 60)
    print("GAME")
    print("=" * 60)
    game = get_game_info(game_id)
    if game:
        print(f"  Game ID:  {game['game_id']}")
        if "date" in game and game["date"]:
            print(f"  Date:     {game['date']}")
        if "teams" in game and game["teams"]:
            score = " @ ".join(
                f"{t['team']} ({t['pts']})" for t in game["teams"]
            )
            print(f"  Score:    {score}")
        elif "matchup" in game and game["matchup"]:
            print(f"  Matchup:  {game['matchup']}")
        if "error" in game:
            print(f"  Error:    {game['error']}")
    else:
        print(f"  Game ID {game_id} not found")


if __name__ == "__main__":
    main()
