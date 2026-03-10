"""
In-memory store for live game state and win probabilities.

- Updated every 5s by the background poll task.
- Read by GET /games (and any other routes that need current state).
"""

from typing import Any

# Latest games list: same shape as your existing /games response.
GAMES_STATE: list[dict[str, Any]] = []

# Win probabilities by game_id: { "game_id": { "home_win_prob": 0.6, "away_win_prob": 0.4 } }
PROBABILITIES_STATE: dict[str, dict[str, float]] = {}

# Probability history per game – one snapshot per poll cycle.
# { game_id: [ {"clock": "7:07 - 3rd", "home_win_prob": 65.2, "away_win_prob": 34.8}, ... ] }
MAX_PROB_HISTORY = 2000
PROBABILITY_HISTORY: dict[str, list[dict[str, Any]]] = {}

# Last in-memory snapshot index persisted to DB per game.
# Used to persist only new snapshots each poll cycle.
LAST_PERSISTED_PROB_INDEX_BY_GAME: dict[str, int] = {}

# Player props by player name for upcoming days
# {'player name': {'bookmaker': {'points': {'over_odds': -120, 'under_odds': 100, 'line': 17.5}}}}
PLAYER_PROPS_STATE: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}   # player name -> bookmaker -> stat -> odds

# Game IDs already saved to database to prevent duplicates
SAVED_FINAL_GAME_IDS: set[str] = set()

# Live/mock props snapshot for /api/props and WS topic "props"
PROPS_SNAPSHOT_STATE: dict[str, Any] = {
    "updated_at": None,
    "projections": [],
}
