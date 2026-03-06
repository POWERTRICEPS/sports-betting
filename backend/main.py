import asyncio
import json
from contextlib import asynccontextmanager
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime

from util import (
    compute_win_probabilities,
    parse_game_data,
    parse_dashboard_game_data,
    merge_gp,
    fetch_espn_lineups,
    fetch_standings_from_espn,
    fetch_games_from_nba,
    fetch_dashboard_games,
    get_player_props as fetch_player_props,

)
import state as app_state

async def update_games_and_probabilities():
    """
    Update the games and probabilities in the in-memory store and broadcast to WebSocket clients.
    Uses lightweight dashboard data for efficiency.
    """
    games = fetch_dashboard_games()
    probabilities = compute_win_probabilities(games)
    app_state.GAMES_STATE.clear()
    app_state.GAMES_STATE.extend(games)
    app_state.PROBABILITIES_STATE.clear()
    app_state.PROBABILITIES_STATE.update(probabilities)
    
    result = merge_gp(games, probabilities)
    games_targets = manager.topic_connection_labels("games")
    print(
        f"[broadcast] topic=games payload=GameWithProbability[] games={len(result)} "
        f"subscribers={len(games_targets)} active_total={len(manager.active_connections)} "
        f"targets={games_targets}"
    )
    # Broadcast to games dashboard
    await manager.broadcast_to_topic("games", result)

    """
    # Broadcast to singel gameID (todo: remove and create separate function to send per game stats needed)
    for game in result:
        game_id = game.get("game_id")
        if game_id:
            topic = f"game:{game_id}"
            topic_targets = manager.topic_connection_labels(topic)
            if topic_targets:
                print(
                    f"[broadcast] topic={topic} payload=GameWithProbability "
                    f"subscribers={len(topic_targets)} targets={topic_targets}"
                )
            await manager.broadcast_to_topic(topic, game)
    """

async def update_subscribed_game_stats():
    """
    Fetch full stats ONLY for subscribed games and broadcast.
    """
    game_ids = get_subscribed_game_ids()

    if not game_ids:
        return
    try:
        # Fetch full detailed game stats
        games = fetch_games_from_nba()

        # Compute win probabilities
        probabilities = compute_win_probabilities(games)

        for game_id in game_ids:
            target = next(
                (g for g in games if g["game_id"] == game_id),
                None
            )
            if not target:
                continue

            merged = merge_gp([target], probabilities)[0]

            topic = f"game:{game_id}"

            # Broadcast only to subscribers
            await manager.broadcast_to_topic(topic, merged)

            print(
                f"[broadcast] detailed topic={topic} "
                f"subs={manager.topic_size(topic)}"
            )

    except Exception as e:
        print(f"detailed update error: {e}")

async def poll_loop():
    """Poll the NBA API every 5 seconds and update the games and probabilities."""
    while True:
        try:
            await update_games_and_probabilities()
        except Exception as e:
            print(f"poll error: {e}")
        
        await asyncio.sleep(5)

# New poll loop       
async def detailed_poll_loop():
    """
    Poll detailed stats for subscribed games.
    """
    while True:
        try:
            await update_subscribed_game_stats()
        except Exception as e:
            print(f"detailed poll loop error: {e}")

        await asyncio.sleep(5)


def get_subscribed_game_ids() -> list[str]:
    """
    Returns list of subscribed game_ids from topics like 'game:{id}'
    """
    ids = []

    for topic in manager.topic_connections.keys():
        if topic.startswith("game:"):
            game_id = topic.split("game:")[1]
            if game_id:
                ids.append(game_id)

    return ids

class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self.topic_connections: dict[str, set[WebSocket]] = {}
        self.connection_topics: dict[WebSocket, set[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        # Keep existing clients working by defaulting to the aggregate stream.
        await self.subscribe(websocket, "games")
        print(
            f"[ws] connected client={self.connection_label(websocket)} "
            f"active_total={len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket):
        topics = list(self.connection_topics.get(websocket, set()))
        for topic in topics:
            await self.unsubscribe(websocket, topic)
        self.connection_topics.pop(websocket, None)
        self.active_connections.discard(websocket)
        print(
            f"[ws] disconnected client={self.connection_label(websocket)} "
            f"active_total={len(self.active_connections)}"
        )

    async def subscribe(self, websocket: WebSocket, topic: str):
        if not topic:
            return
        self.topic_connections.setdefault(topic, set()).add(websocket)
        self.connection_topics.setdefault(websocket, set()).add(topic)
        print(
            f"[ws] subscribe client={self.connection_label(websocket)} "
            f"topic={topic} subscribers={self.topic_size(topic)}"
        )

    async def unsubscribe(self, websocket: WebSocket, topic: str):
        subscribers = self.topic_connections.get(topic)
        if not subscribers:
            return
        subscribers.discard(websocket)
        if not subscribers:
            self.topic_connections.pop(topic, None)

        topics = self.connection_topics.get(websocket)
        if topics:
            topics.discard(topic)
            if not topics:
                self.connection_topics.pop(websocket, None)
        print(
            f"[ws] unsubscribe client={self.connection_label(websocket)} "
            f"topic={topic} subscribers={self.topic_size(topic)}"
        )

    def topic_size(self, topic: str) -> int:
        return len(self.topic_connections.get(topic, set()))

    def connection_label(self, websocket: WebSocket) -> str:
        client = websocket.client
        if client:
            return f"{client.host}:{client.port}"
        return f"ws:{id(websocket)}"

    def topic_connection_labels(self, topic: str) -> list[str]:
        return [self.connection_label(c) for c in self.topic_connections.get(topic, set())]

    async def broadcast_to_topic(self, topic: str, payload: Any):
        subscribers = list(self.topic_connections.get(topic, set()))
        if not subscribers:
            return
        txt = json.dumps(payload)
        dead_connections: list[WebSocket] = []
        for c in subscribers:
            try:
                await c.send_text(txt)
            except Exception:
                dead_connections.append(c)
        for c in dead_connections:
            await self.disconnect(c)


manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    dashboard_task = asyncio.create_task(poll_loop())
    detailed_task = asyncio.create_task(detailed_poll_loop())
    props_task = asyncio.create_task(props_poll_loop())
    try:
        yield
    finally:
        dashboard_task.cancel()
        detailed_task.cancel()
        props_task.cancel()
        try:
            await dashboard_task
            await detailed_task
            await props_task
        except asyncio.CancelledError:
            pass
        
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://pj09-sports-betting.vercel.app", "https://pj09-sports-betting-2enq4id18-kevins-projects-8b1f5231.vercel.app"],
    allow_origin_regex=r"^https://pj09-sports-betting(?:-[a-z0-9-]+)?\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health")
def health():
    return {"health": "healthy"}

@app.get("/api/games")
def games():
    """
    Returns current games with dashboard-viewable data only:
    - game_id, status
    - team names, abbreviations, records (wins/losses)
    - current scores
    - win probabilities
    
    Data is from in-memory store updated every 5s by background poll.
    Gracefully handles no available games by returning empty list.
    """
    print("games route hit")
    g = list(app_state.GAMES_STATE)
    p = dict(app_state.PROBABILITIES_STATE)
    
    # If in-memory store is empty (e.g., on first request), fetch fresh data
    if not g:
        try:
            g = fetch_dashboard_games()
            p = compute_win_probabilities(g)
            app_state.GAMES_STATE.extend(g)
            app_state.PROBABILITIES_STATE.update(p)
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []
    
    # Gracefully handle no games scenario
    if not g:
        return []
    
    return merge_gp(g, p)

@app.get("/api/props/{player_name}")
def get_player_props(player_name: str):
    """
    Returns player PTS, REB, and AST props for a given player name.
    Also includes over/under lines from different bookmakers (platforms).
    """
    return fetch_player_props(player_name)

# Standings route
@app.get("/api/standings")
def standings():
    """
    Retrieve current NBA league standings grouped by conference.
    """
    try:
        return fetch_standings_from_espn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

# Starting Lineups Route (ESPN-sourced)
@app.get("/api/v1/lineups/{game_date}")
def get_lineups(game_date: str):
    # Validate date format
    if not game_date or len(game_date) != 8 or not game_date.isdigit():
        return {
            "error": "Invalid date format. Use YYYYMMDD (e.g., '20260212')",
            "date": game_date,
            "games": []
        }

    try:
        return fetch_espn_lineups(game_date)
    except requests.exceptions.Timeout:
        return {
            "error": "Request timeout. ESPN may be slow or unavailable.",
            "date": game_date,
            "games": []
        }
    except Exception as e:
        print(f"Error fetching starting lineups: {e}")
        return {
            "error": str(e),
            "date": game_date,
            "games": []
        }

# Endpoint for specific game using game_id
@app.get("/api/games/stats/{game_id}")
def single_game_stats(game_id: str):
    """
    Returns full normalized stats + win probability for ONE specific game.
    Uses full game data (not dashboard lightweight version).
    First checks in-memory dashboard store, then fetches full stats if needed.
    """
    # Check if game exists in dashboard store first
    g_dashboard = list(app_state.GAMES_STATE)
    game_exists = any(game["game_id"] == game_id for game in g_dashboard)
    
    if not game_exists:
        return {"error": "Invalid game_id"}, 404
    
    # Fetch full stats for this specific game
    try:
        g_full = fetch_games_from_nba()
        p = compute_win_probabilities(g_full)
        
        target = next((game for game in g_full if game["game_id"] == game_id), None)
        
        if not target:
            return {"error": "Invalid game_id"}, 404
        
        result = merge_gp([target], p)
        return result[0]
    except Exception as e:
        print(f"Error fetching game stats: {e}")
        return {"error": "Failed to fetch game stats"}, 500
    
def _build_mock_props_payload() -> dict[str, Any]:
    return {
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "projections": [
            {
                "game_id": "401000001",
                "player_id": "203999",
                "player_name": "Nikola Jokic",
                "team_abbr": "DEN",
                "opponent_abbr": "LAL",
                "is_starter": True,
                "projected_pts": 28.4,
                "projected_reb": 12.1,
                "projected_ast": 9.3,
                "source": "mock",
            },
            {
                "game_id": "401000001",
                "player_id": "2544",
                "player_name": "LeBron James",
                "team_abbr": "LAL",
                "opponent_abbr": "DEN",
                "is_starter": True,
                "projected_pts": 26.7,
                "projected_reb": 7.8,
                "projected_ast": 8.0,
                "source": "mock",
            },
        ],
    }


async def update_player_props():
    """
    Placeholder updater.
    """
    payload = _build_mock_props_payload()
    app_state.PROPS_SNAPSHOT_STATE.clear()
    app_state.PROPS_SNAPSHOT_STATE.update(payload)

    await manager.broadcast_to_topic("props", payload)


async def props_poll_loop():
    """Poll/update props every 5 seconds."""
    while True:
        try:
            await update_player_props()
        except Exception as e:
            print(f"props poll loop error: {e}")
        await asyncio.sleep(5)


@app.get("/api/props")
def props():
    """
    Returns current props snapshot (mock for now).
    """
    if not app_state.PROPS_SNAPSHOT_STATE.get("projections"):
        app_state.PROPS_SNAPSHOT_STATE.update(_build_mock_props_payload())
    return app_state.PROPS_SNAPSHOT_STATE

  
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()
            if not message:
                continue

            action = None
            topic = None
            try:
                payload = json.loads(message)
                if isinstance(payload, dict):
                    action = payload.get("action") or payload.get("type")
                    topic = payload.get("topic")
            except json.JSONDecodeError:
                # Ignore non-JSON heartbeat text.
                continue

            if action == "subscribe" and isinstance(topic, str):
                await manager.subscribe(websocket, topic)
                await websocket.send_json({"ok": True, "action": "subscribe", "topic": topic})
            elif action == "unsubscribe" and isinstance(topic, str):
                await manager.unsubscribe(websocket, topic)
                await websocket.send_json({"ok": True, "action": "unsubscribe", "topic": topic})
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
