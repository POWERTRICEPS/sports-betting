"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import type {
  Game,
  ConnectionStatus,
  StandingsResponse,
} from "./types";

const BACKEND_URL = "pj09-sports-betting.onrender.com";
// const BACKEND_URL = "localhost:8000";
const isLocal = BACKEND_URL.startsWith("localhost") || BACKEND_URL.startsWith("127.0.0.1");
const WS_URL = isLocal ? `ws://${BACKEND_URL}/ws` : `wss://${BACKEND_URL}/ws`;
const API_URL = isLocal
  ? `http://${BACKEND_URL}/api/games`
  : `https://${BACKEND_URL}/api/games`;
const STANDINGS_API_URL = isLocal
  ? `http://${BACKEND_URL}/api/standings`
  : `https://${BACKEND_URL}/api/standings`;
const RECONNECT_INTERVAL = 5000; // 5 second interval
const MAX_RECONNECT_ATTEMPTS = 10;

type GameDataContextValue = {
  games: Game[];
  gamesLoading: boolean;
  status: ConnectionStatus;
  error: string | null;
  reconnect: () => void;
  standings: StandingsResponse | null;
  standingsLoading: boolean;
};

const GameDataContext = createContext<GameDataContextValue | null>(null);

export function GameDataProvider({ children }: { children: React.ReactNode }) {
  const [games, setGames] = useState<Game[]>([]);
  const [gamesLoading, setGamesLoading] = useState<boolean>(true);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [error, setError] = useState<string | null>(null);
  const [standings, setStandings] = useState<StandingsResponse | null>(null);
  const [standingsLoading, setStandingsLoading] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const gamesRef = useRef<Game[]>([]);

  // used for initial data population
  const fetchGames = useCallback(async () => {
    setGamesLoading(true);
    try {
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const nextGames: Game[] = Array.isArray(data)
        ? data
        : (data?.games ?? []);
      gamesRef.current = nextGames;
      setGames(nextGames);
    } catch (e) {
      console.error("Fetch games failed:", e);
      setError("Failed to fetch games");
    } finally {
      setGamesLoading(false);
    }
  }, []);

  const fetchStandings = useCallback(async () => {
    try {
      setStandingsLoading(true);
      const res = await fetch(STANDINGS_API_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();

      if (Array.isArray(json) && json.length > 0) {
        setStandings(json[0] as StandingsResponse);
      }
    } catch (e) {
      console.error("Fetch standings failed:", e);
    } finally {
      setStandingsLoading(false);
    }
  }, []);

  const connect = useCallback(() => {
    try {
      setStatus("connecting");
      setError(null);

      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connected");
        setStatus("connected");
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (!Array.isArray(data)) {
            console.warn("Unexpected game data format from WebSocket:", data);
            return;
          }

          const prevGames = gamesRef.current;
          gamesRef.current = data;
          setGames(data);

          const hasNewlyFinalGame = data.some((game) => {
            const prev = prevGames.find((g) => g.game_id === game.game_id);
            const prevStatus = (prev?.status ?? "").toLowerCase();
            const nextStatus = (game.status ?? "").toLowerCase();

            return !prevStatus.includes("final") && nextStatus.includes("final");
          });

          if (hasNewlyFinalGame) {
            fetchStandings();
          }
        } catch (err) {
          console.error("Failed to parse game data:", err);
          setError("Failed to parse game data");
        }
      };

      ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        setStatus("error");
        setError("WebSocket connection error");
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setStatus("disconnected");

        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, RECONNECT_INTERVAL);
        } else {
          setError(
            "Max reconnection attempts reached. Backend may not be ready.",
          );
        }
      };
    } catch (err) {
      console.error("Failed to create WebSocket:", err);
      setStatus("error");
      setError("Failed to create WebSocket connection");
    }
  }, [fetchStandings]);

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0;
    if (wsRef.current) {
      wsRef.current.close();
    }
    connect();
  }, [connect]);

  useEffect(() => {
    fetchGames();
    fetchStandings();
  }, [fetchGames, fetchStandings]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const value: GameDataContextValue = {
    games,
    gamesLoading,
    status,
    error,
    reconnect,
    standings,
    standingsLoading,
  };

  return (
    <GameDataContext.Provider value={value}>
      {children}
    </GameDataContext.Provider>
  );
}

export function useGameData(): GameDataContextValue {
  const ctx = useContext(GameDataContext);
  if (!ctx) {
    throw new Error("useGameData must be used within GameDataProvider");
  }
  return ctx;
}
