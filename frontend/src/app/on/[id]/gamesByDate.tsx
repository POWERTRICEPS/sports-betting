"use client";

import GameCard from "../../games/GameCard";
import Standings from "../../standings/Standings";
import { mockGames } from "../../games/mock";
import { useEffect, useState } from "react";
import { Game } from "@/app/types";
import DateNav from "@/app/components/DateNav";

// const BACKEND_URL = "pj09-sports-betting.onrender.com";
const BACKEND_URL = "localhost:8000";
const isLocal =
  BACKEND_URL.startsWith("localhost") || BACKEND_URL.startsWith("127.0.0.1");
const API_URL = isLocal ? `http://${BACKEND_URL}` : `https://${BACKEND_URL}`;

export default function GamesByDate({ id }: { id: string }) {
  const [displayGames, setDisplayGames] = useState<Game[]>([]);

  useEffect(() => {
    async function fetchGameByDateId() {
      const res = await fetch(`${API_URL}/api/games/${id}`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();

      setDisplayGames(data.length ? data : mockGames);
    }
    fetchGameByDateId();
  }, [id]);

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
            {displayGames.map((game) => (
              <GameCard key={game.game_id} data={game} />
            ))}
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
