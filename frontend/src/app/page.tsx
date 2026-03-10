"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import GameCard from "./games/GameCard";
import { GameCardsSkeleton, GamesListEmptyState } from "./games/GameStates";
import Standings from "./standings/Standings";
import { useGameData } from "./GameDataProvider";
import DateNav from "./components/DateNav";

export default function GamesPage() {
  const { games, gamesLoading, status, error } = useGameData();
  const [pinnedGames, setPinnedGames] = useState<string[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const stored = JSON.parse(localStorage.getItem("pinnedGames") || "[]") as string[];
    setPinnedGames(Array.isArray(stored) ? stored : []);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || games.length === 0) return;
    setPinnedGames((prev) => {
      const valid = prev.filter((id) => games.some((g) => g.game_id === id));
      if (valid.length !== prev.length) {
        localStorage.setItem("pinnedGames", JSON.stringify(valid));
      }
      return valid;
    });
  }, [games]);

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

  const displayGames = useMemo(() => {
    const sorted = [...games];
    if (pinnedGames.length === 0) return sorted;
    sorted.sort((a, b) => {
      const aPinned = pinnedGames.includes(a.game_id);
      const bPinned = pinnedGames.includes(b.game_id);
      if (aPinned && !bPinned) return -1;
      if (!aPinned && bPinned) return 1;
      return 0;
    });
    return sorted;
  }, [games, pinnedGames]);

  let today = new Date();

  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-950 dark:bg-zinc-950 dark:text-zinc-50 p-6 pt-20">
      <div className="mx-auto max-w-7xl">

        <DateNav date={today} />

        <div className="mt-6 grid grid-cols-6 gap-24">
          {/* LEFT: Game cards (5/7) */}
          <div className="col-span-4 grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
            {gamesLoading ? (
              <GameCardsSkeleton />
            ) : displayGames.length > 0 ? (
              displayGames.map((game) => (
                <GameCard
                  key={game.game_id}
                  data={game}
                  isPinned={pinnedGames.includes(game.game_id)}
                  onTogglePin={onTogglePin}
                />
              ))
            ) : (
              <GamesListEmptyState message="No games available today." />
            )}
          </div>

          {/* RIGHT: NBA Standings (2/7) */}
          <div className="col-span-2">
             <Standings />
          </div>
        </div>

        <div className="mt-6 text-sm text-zinc-500 dark:text-zinc-400">
          Status: {status}
          {error ? ` • ${error}` : null}
        </div>

        <section className="mt-8 border-t border-zinc-200 pt-6 text-center text-sm leading-7 text-zinc-600 dark:border-zinc-700 dark:text-zinc-300">
          <p>
            This app is for informational and educational purposes only. Stats,
            win probabilities, and player projections are estimates and may be
            delayed, incomplete, or inaccurate. Nothing shown in this app is
            financial, betting, or legal advice, and no outcome is guaranteed.
          </p>
          <p className="mt-4">
            Users are responsible for verifying all information with official
            sources and for following the laws and age requirements in their
            location. This project is not a sportsbook and does not accept
            wagers.
          </p>
          <p className="mt-4">
            If gambling is causing harm, help is available 24/7 in the U.S. at{" "}
            <a
              href="tel:18004262537"
              className="font-semibold text-cyan-700 hover:underline dark:text-cyan-400"
            >
              1-800-GAMBLER (1-800-426-2537)
            </a>{" "}
            or by visiting{" "}
            <a
              href="https://www.1800gambler.net"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-cyan-700 hover:underline dark:text-cyan-400"
            >
              1800gambler.net
            </a>
            .
          </p>
        </section>
      </div>
    </main>
  );
}
/* <div className="">
        <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-white">
          GC1.
        </h1>
      </div>
      <div className="a2 rounded-lg border border-zinc-200 dark:border-zinc-800 p-4">
        <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-white">
          GC2
        </h1>
      </div>
*/
