# Player Props (Odds & Lines)

## Summary

Player props are fetched in `backend/util.py` via `get_player_props(player_name)` and exposed by `GET /api/props/{player_name}`. The backend returns **market odds and over/under lines** for points, rebounds, and assists from the SportsGameOdds API. No in-backend probability model is applied; the response is a direct mapping of bookmaker odds and lines per stat.

Output structure:

- One object per requested player, keyed by stat: `points`, `rebounds`, `assists`.
- Each stat has `over` and `under`, each with per-bookmaker `odds` and `line` (over/under value).

Scale / semantics:

- `line`: the over/under number (e.g. 24.5 points).
- `odds`: the bookmaker’s odds for that side (e.g. American or decimal, as returned by the API).

## Data Source

**SportsGameOdds API** (`https://api.sportsgameodds.com/v2/events`):

- Required: `apiKey`, `leagueID=NBA`, `oddsAvailable=true`.
- Player is identified by **player entity ID**: `FIRSTNAME_LASTNAME_1_NBA` (e.g. `JALEN_DUREN_1_NBA`), built from the player’s full name in `get_player_props`.
- **oddIDs** requested per stat (points, rebounds, assists):  
  `{stat}-{player_entity_id}-game-ou-over` and `{stat}-{player_entity_id}-game-ou-under`.

One request is made per stat (three requests per player total). Responses are merged into a single payload; if a stat has no data, that stat is omitted from the result.

## Runtime Behavior

### Successful response

- For each of `points`, `rebounds`, `assists`, the function requests the corresponding over/under oddIDs.
- From each response, `data["data"][0]["odds"]` is read; the over and under entries’ `byBookmaker` data is normalized to `{ bookmaker: { "odds", "line" } }`.
- Result: `{ "points": { "over": {...}, "under": {...} }, "rebounds": {...}, "assists": {...} }`.

### Missing or empty data

- If the API returns no events for a stat (`data["data"]` empty or missing), that stat is skipped; the rest are still included.
- No explicit “probability” is computed; only odds and lines from the API are returned.

### Player name handling

- `player_entity_id` is derived by uppercasing and joining the name with underscores, then appending `_1_NBA` (e.g. `"Jalen Duren"` → `JALEN_DUREN_1_NBA`). The API must recognize this ID for the player to have props.

## Contract Example

```json
{
  "points": {
    "over": {
      "draftkings": { "odds": -110, "line": 24.5 },
      "fanduel": { "odds": -112, "line": 24.5 }
    },
    "under": {
      "draftkings": { "odds": -110, "line": 24.5 },
      "fanduel": { "odds": -108, "line": 24.5 }
    }
  },
  "rebounds": {
    "over": { "draftkings": { "odds": -115, "line": 10.5 } },
    "under": { "draftkings": { "odds": -105, "line": 10.5 } }
  },
  "assists": {
    "over": { "fanduel": { "odds": -118, "line": 5.5 } },
    "under": { "fanduel": { "odds": -104, "line": 5.5 } }
  }
}
```

## Related ML Models

PTS, REB, and AST **regression** models exist in `ml/models_PTS/`, `ml/models_REB/`, and `ml/models_AST/` (e.g. XGBoost). They predict **final stat values** (e.g. `final_points`) from in-game and season features (e.g. `seconds_remaining`, `current_points`, `season_ppg`, `season_fga`, etc.).
