# Win Probability Model

## Summary

Win probabilities are computed in `backend/util.py` and attached to each game record.

Output fields:
- `home_win_prob`
- `away_win_prob`

Current scale:
- Percentage scale from `0` to `100`.
- `away_win_prob = 100 - home_win_prob`.

## Model Features

The in-game model (`ml/model.joblib`) uses **9 features** in this order:

| Feature | Description |
|--------|-------------|
| `SECONDS_REMAINING` | Time left in the game (seconds), derived from status/clock. |
| `HOME_SCORE` | Home team’s current score. |
| `AWAY_SCORE` | Away team’s current score. |
| `HOME_WINS` | Home team’s **season record (wins)**. |
| `HOME_LOSSES` | Home team’s **season record (losses)**. |
| `AWAY_WINS` | Away team’s **season record (wins)**. |
| `AWAY_LOSSES` | Away team’s **season record (losses)**. |
| `HOME_L10_WINS` | Home team’s **last 10 games – wins**. |
| `AWAY_L10_WINS` | Away team’s **last 10 games – wins**. |

**Data sources (runtime):**
- Scores and status come from the ESPN scoreboard.
- Season records (home/away wins and losses) come from the ESPN event’s competition records (overall/total).
- L10 wins come from ESPN standings (“Last Ten Games”), mapped by team abbreviation; see `_l10_by_abbrev_from_espn_standings()` in `util.py`.

Training uses the same feature set (e.g. in `ml/wp_models/` and `ml/preprocessing/scrape_wp.py`). `PERIOD` and `POINT_DIFF` are **not** used at inference; only `SECONDS_REMAINING` encodes time.

## Runtime Behavior

### Final games
If status is `Final`:
- Home team gets `100` when `home_score >= away_score`, else `0`.
- Away team is the complement.

### In-progress games
If `ml/model.joblib` exists:
- The 9 features above are built from the game object and passed to the model.
- Probability comes from `predict_proba` (or `predict` for NN) and is converted to percent.

If model file is missing:
- Fallback returns `50, 50` for non-final games (see `calculate()` in `util.py`).

## Status Parsing

`parse_status(status: str)` maps status text to `(period, seconds_remaining)`.

Handled values include:
- `Pregame`, `Scheduled`
- `Q1 mm:ss`, `Q2 mm:ss`, `Q3 mm:ss`, `Q4 mm:ss`
- `Halftime`
- `Overtime`, `OT`, `2OT`, `3OT`, and optional OT clock values
- `Final`

Unknown formats currently return `(None, None)` and produce a `0,0` probability output in `calculate`.

## Contract Example

```json
{
  "home_win_prob": 63.2,
  "away_win_prob": 36.8
}
```

## Integration Notes

- Frontend should treat these values as percentages, not unit probabilities.
- When the model file is missing, non-final games return `50, 50` (even split).
- Games passed to `compute_win_probabilities()` must include `home_wins`, `home_losses`, `away_wins`, `away_losses`, and (for best results) `home_l10_wins`, `away_l10_wins`; the latter are added by `fetch_games_with_win_prob()` from ESPN standings.
