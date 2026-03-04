from nba_api.stats.endpoints import playercareerstats

print("A")

# Nikola Jokić
career = playercareerstats.PlayerCareerStats(player_id='203999')

print("B")

# pandas data frames (optional: pip install pandas)
career.season_totals_regular_season.get_data_frame()

# json
career.get_json()

# dictionary
career.get_dict()