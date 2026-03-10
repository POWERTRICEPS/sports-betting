"use client";

import GameCard from "../../games/GameCard";
import {
  GameCardsSkeleton,
  GamesListEmptyState,
  GamesListErrorState,
} from "../../games/GameStates";
import Standings from "../../standings/Standings";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Game } from "@/app/types";
import DateNav from "@/app/components/DateNav";

const BACKEND_URL = "pj09-sports-betting.onrender.com";
// const BACKEND_URL = "localhost:8000";
const isLocal =
  BACKEND_URL.startsWith("localhost") || BACKEND_URL.startsWith("127.0.0.1");
const API_URL = isLocal ? `http://${BACKEND_URL}` : `https://${BACKEND_URL}`;

export default function GamesByDate({ id }: { id: string }) {
  const [displayGames, setDisplayGames] = useState<Game[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [pinnedGames, setPinnedGames] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = JSON.parse(localStorage.getItem("pinnedGames") || "[]") as string[];
    setPinnedGames(Array.isArray(stored) ? stored : []);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || displayGames.length === 0) return;
    setPinnedGames((prev) => {
      const valid = prev.filter((gameId) =>
        displayGames.some((game) => game.game_id === gameId),
      );
      if (valid.length !== prev.length) {
        localStorage.setItem("pinnedGames", JSON.stringify(valid));
      }
      return valid;
    });
  }, [displayGames]);

  const onTogglePin = useCallback((gameId: string) => {
    setPinnedGames((prev) => {
      const next = prev.includes(gameId)
        ? prev.filter((id) => id !== gameId)
        : [...prev, gameId];
      if (typeof window !== "undefined") {
        localStorage.setItem("pinnedGames", JSON.stringify(next));
      }
      return next;
    });
  }, []);

  const fetchGameByDateId = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/games/${id}`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setDisplayGames(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("Failed to fetch games by date:", e);
      setDisplayGames([]);
      setError("Failed to load games for this date.");
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchGameByDateId();
  }, [fetchGameByDateId]);

  const sortedDisplayGames = useMemo(() => {
    const sorted = [...displayGames];
    if (pinnedGames.length === 0) return sorted;
    sorted.sort((a, b) => {
      const aPinned = pinnedGames.includes(a.game_id);
      const bPinned = pinnedGames.includes(b.game_id);
      if (aPinned && !bPinned) return -1;
      if (!aPinned && bPinned) return 1;
      return 0;
    });
    return sorted;
  }, [displayGames, pinnedGames]);

  const today = new Date(
    Number(id.slice(0, 4)),
    Number(id.slice(4, 6)) - 1,
    Number(id.slice(6, 8)),
  );

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-950 dark:bg-zinc-950 dark:text-zinc-50 p-6 pt-20">
      <div className="mx-auto max-w-7xl">
        <DateNav date={today} />

        <div key={id} className="mt-6 grid grid-cols-6 gap-24">
          {/* LEFT: Game cards (5/7) */}
          <div className="col-span-4 grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            {isLoading ? (
              <GameCardsSkeleton />
            ) : error ? (
              <GamesListErrorState message={error} onRetry={fetchGameByDateId} />
            ) : sortedDisplayGames.length > 0 ? (
              sortedDisplayGames.map((game) => (
                <GameCard
                  key={game.game_id}
                  data={game}
                  isPinned={pinnedGames.includes(game.game_id)}
                  onTogglePin={onTogglePin}
                />
              ))
            ) : (
              <GamesListEmptyState message="No games available for this date." />
            )}
          </div>

          {/* RIGHT: NBA Standings (2/7) */}
          <div className="col-span-2">
            <Standings />
          </div>
        </div>
      </div>
    </main>
  );
}
