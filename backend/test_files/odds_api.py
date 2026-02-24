import os
import requests
from dotenv import load_dotenv
from typing import Any
import json

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

def get_player_props(player_name: str) -> dict[str, Any]:
    """
    Get player props from The Odds API. 
    Retrieves points, rebounds, and assist O/U lines for a given player for different betting platforms. 
    https://api.sportsgameodds.com/v2/events?apiKey=API_KEY_HERE&leagueID=NBA&oddsAvailable=true&oddIDs=points-PLAYER_ID-game-ou-over,points-PLAYER_ID-game-ou-under
    """
    player_name_chunks = player_name.split(" ")
    # remove 'jr' or other suffixes from player name if present
    if len(player_name_chunks) > 2:
        player_name = player_name_chunks[0] + " " + player_name_chunks[1]
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

    payload: dict[str, Any] = {}
    for stat in ["points", "rebounds", "assists"]:
        data = get_stat_odds(stat)
        over_key = f"{stat}-{player_entity_id}-game-ou-over"
        under_key = f"{stat}-{player_entity_id}-game-ou-under"
        over_by_book = data[over_key]["byBookmaker"]
        under_by_book = data[under_key]["byBookmaker"]

        payload[stat] = {}
        for platform in over_by_book:
            if platform not in under_by_book:
                continue
            payload[stat][platform] = {
                "line": over_by_book[platform]["overUnder"],
                "over_odds": over_by_book[platform]["odds"],
                "under_odds": under_by_book[platform]["odds"],
            }

    return payload

res = json.dumps(get_player_props("jabari smith"), indent=4)
print(res)