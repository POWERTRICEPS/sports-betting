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

# Player props by player name for upcoming days
# {'player name': {'bookmaker': {'points': {'over_odds': -120, 'under_odds': 100, 'line': 17.5}}}}
PLAYER_PROPS_STATE: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}   # player name -> bookmaker -> stat -> odds

# Probability history by game_id — accumulated every poll cycle.
# Each entry: { "home": float, "away": float, "homeScore": int|None, "awayScore": int|None, "label": str }
# Lives as long as the server process runs (matches ESPN scoreboard lifespan).
PROB_HISTORY_STATE: dict[str, list[dict[str, Any]]] = {}

# Track which final games have already been saved to the database
# so we don't re-save them on every poll cycle.
SAVED_FINAL_GAME_IDS: set[str] = set()

# Current props snapshot (mock or live) — broadcast via WebSocket topic "props".
PROPS_SNAPSHOT_STATE: dict[str, Any] = {}
