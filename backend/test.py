from util import fetch_espn_lineups, get_player_props

# game_date = "20260302"

# # print("Date: ", lineups["date"])
# # print("Lineup Status: ", lineups["lineup_status"])
# # print("Total Games: ", lineups["total_games"])

# # for game in lineups["games"]:
# #     print(game)
# #     print()


# lineups = fetch_espn_lineups(game_date)
# if not lineups:
#     print("No lineups found")
#     exit()

# def get_player_name(player_name: str) -> str:
#     """
#     Parses player name to not include suffixes (e.g. Jr, III, etc.)
#     """
#     player_name_components = player_name.split(" ")
#     if len(player_name_components) > 2:
#         return player_name_components[0] + " " + player_name_components[1]
#     return player_name

# props: dict[str, dict[str, any]] = {}

# for game in lineups["games"]:
#     for side in ("home_team", "away_team"):
#         team = game.get(side) or {}
#         team_abbrev = team.get("team_abbreviation")
#         starters = team.get("starters") or []

#         if not team_abbrev:
#             continue

#         team_props: dict[str, any] = {}
#         for player in starters:
#             raw_name = player.get("name", "")
#             player_name = get_player_name(raw_name)
#             player_props = get_player_props(player_name)
#             team_props[player_name] = player_props

#         props[team_abbrev] = team_props

# print(props)