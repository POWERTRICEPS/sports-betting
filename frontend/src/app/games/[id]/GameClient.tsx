"use client";

import Link from "next/link";
import Image from "next/image";
import { Game } from "@/app/types";
import { mockGames } from "../mock";
import { useEffect, useRef, useState } from "react";
import WinProbabilityGraph from "./WinProbabilityGraph";

const BACKEND_URL = "pj09-sports-betting.onrender.com";
const isLocal =
  BACKEND_URL.startsWith("localhost") || BACKEND_URL.startsWith("127.0.0.1");
const WS_URL = isLocal ? `ws://${BACKEND_URL}/ws` : `wss://${BACKEND_URL}/ws`;
const API_URL = isLocal ? `http://${BACKEND_URL}` : `https://${BACKEND_URL}`;

export default function GameClient({ id }: { id: string }) {
  const imgSize = 150;
  const [game, setGame] = useState<Game | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initial HTTP fetch for immediate data on page load
  useEffect(() => {
    async function fetchGame() {
      try {
        const res = await fetch(`${API_URL}/api/games/stats/${id}`);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();
        setGame(data);
      } catch (err) {
        console.error("Failed to fetch game data:", err);
        const fallbackGame = mockGames[0];
        setGame(fallbackGame);
      }
    }
    fetchGame();
  }, [id]);

  // WebSocket subscription for live updates (single game only)
  useEffect(() => {
    const topic = `game:${id}`;

    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log(
          `[GameClient] WebSocket connected, subscribing to ${topic}`,
        );
        ws.send(JSON.stringify({ type: "subscribe", topic }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("Websocket message received:", data);
          if (data.ok !== undefined) return;
          if (Array.isArray(data)) return;
          if (data && typeof data === "object" && data.game_id === id) {
            console.log("Setting game data from websocket:", data);
            setGame(data);
          }
        } catch (err) {
          console.error("[GameClient] Failed to parse WS message:", err);
        }
      };

      ws.onerror = (event) => {
        console.error("[GameClient] WebSocket error:", event);
      };

      ws.onclose = () => {
        console.log(`[GameClient] WebSocket closed for ${topic}`);
      };
    }

    connect();

    // Cleanup: unsubscribe and close on unmount or when id changes
    return () => {
      const ws = wsRef.current;
      if (ws) {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "unsubscribe", topic }));
        }
        ws.close();
        wsRef.current = null;
      }
    };
  }, [id]);

  return (
    <div className="min-h-screen bg-white dark:bg-zinc-950 p-6 pt-20 text-gray-900 dark:text-zinc-100">
      <div className="absolute top-20 left-6">
        <Link
          href="/"
          className="inline-flex items-center gap-2 bg-blue-900/75 hover:bg-blue-900 text-white font-semibold py-2 px-4 rounded-lg shadow-md backdrop-blur-md transition-all duration-200"
        >
          <span className="text-lg leading-none">←</span>
          Back to Games
        </Link>
      </div>
      <div className="mx-auto max-w-7xl"></div>
      <div className="mx-auto max-w-7xl">
        <div className="rounded-2xl bg-white dark:bg-zinc-900 shadow-sm border border-gray-200 dark:border-zinc-700 p-8 sm:p-10">
          <div className="flex items-center justify-between gap-8">
            {/* Away Team */}
            <div className="flex-1 text-center">
              {game && (
                <Image
                  src={`https://a1.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/scoreboard/${game?.away_abbreviation}.png&h=456&w=456`}
                  alt={`${game?.away_team} logo`}
                  width={180}
                  height={180}
                  className="mx-auto mb-4"
                />
              )}
              <div className="text-xs font-bold uppercase tracking-widest text-gray-500 dark:text-zinc-400">
                {game?.away_city}
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-zinc-100">
                {game?.away_team}
              </div>
              <div className="text-sm text-gray-500 dark:text-zinc-400">
                {game?.away_wins}-{game?.away_losses}
              </div>
            </div>

            {/* Score + Game Info */}
            <div className="flex flex-col items-center gap-6">
              {/* Main Score */}
              <div className="flex items-center gap-6">
                <div className="text-6xl font-extrabold text-gray-900 dark:text-zinc-100 tracking-tight">
                  {game?.away_score}
                </div>
                <div className="text-3xl font-semibold text-gray-400 dark:text-zinc-500">
                  -
                </div>
                <div className="text-6xl font-extrabold text-gray-900 dark:text-zinc-100 tracking-tight">
                  {game?.home_score}
                </div>
              </div>

              {/* Status */}
              <div className="rounded-full bg-gray-100 dark:bg-zinc-800 px-4 py-1 text-xs font-bold tracking-widest text-gray-700 dark:text-zinc-300">
                {game?.status}
              </div>

              {/* Quarter Table */}
              <div className="mt-2">
                <table className="text-base border-separate border-spacing-y-2">
                  <thead>
                    <tr className="text-gray-500 dark:text-zinc-400 uppercase text-xs tracking-wide">
                      <th className="px-4 text-left">Team</th>
                      <th className="px-4 text-center">Q1</th>
                      <th className="px-4 text-center">Q2</th>
                      <th className="px-4 text-center">Q3</th>
                      <th className="px-4 text-center">Q4</th>
                      <th className="px-4 text-center font-semibold">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="px-4 font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.away_team}
                      </td>
                      <td className="px-4 text-center text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.away_q1 ?? "-"}
                      </td>
                      <td className="px-4 text-center text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.away_q2 ?? "-"}
                      </td>
                      <td className="px-4 text-center text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.away_q3 ?? "-"}
                      </td>
                      <td className="px-4 text-center text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.away_q4 ?? "-"}
                      </td>
                      <td className="px-4 text-center text-xl font-bold text-zinc-900 dark:text-zinc-100">
                        {game?.away_score}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-4 font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.home_team}
                      </td>
                      <td className="px-4 text-center text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.home_q1 ?? "-"}
                      </td>
                      <td className="px-4 text-center text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.home_q2 ?? "-"}
                      </td>
                      <td className="px-4 text-center text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.home_q3 ?? "-"}
                      </td>
                      <td className="px-4 text-center text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                        {game?.home_q4 ?? "-"}
                      </td>
                      <td className="px-4 text-center text-xl font-bold text-zinc-900 dark:text-zinc-100">
                        {game?.home_score}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Home Team */}
            <div className="flex-1 text-center">
              {game && (
                <Image
                  src={`https://a1.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/scoreboard/${game?.home_abbreviation}.png&h=456&w=456`}
                  alt={`${game?.home_team} logo`}
                  width={180}
                  height={180}
                  className="mx-auto mb-4"
                />
              )}
              <div className="text-xs font-bold uppercase tracking-widest text-gray-500 dark:text-zinc-400">
                {game?.home_city}
              </div>
              <div className="text-2xl font-bold text-gray-900 dark:text-zinc-100">
                {game?.home_team}
              </div>
              <div className="text-sm text-gray-500 dark:text-zinc-400">
                {game?.home_wins}-{game?.home_losses}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto mt-10 max-w-6xl text-gray-700 dark:text-zinc-300">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Game Leaders */}
          <div className="rounded-2xl bg-white dark:bg-zinc-900 shadow-sm border border-gray-200 dark:border-zinc-700 p-6">
            <h3 className="text-lg font-bold text-gray-900 dark:text-zinc-100 mb-6 text-center">
              Game Leaders
            </h3>

            {/* Team Headers */}
            <div className="grid grid-cols-3 mb-4">
              <div className="text-left font-semibold text-gray-600 dark:text-zinc-400 uppercase tracking-wide">
                {game?.away_team}
              </div>
              <div></div>
              <div className="text-right font-semibold text-gray-600 dark:text-zinc-400 uppercase tracking-wide">
                {game?.home_team}
              </div>
            </div>

            <div className="space-y-4">
              {/* Points */}
              <div className="grid grid-cols-3 items-center">
                <div className="text-left">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {game?.away_leader_pts_name ?? "-"}
                  </span>
                  <span className="ml-2 text-gray-500 dark:text-zinc-400">
                    {game?.away_leader_pts_val ?? ""}
                  </span>
                </div>

                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  Points
                </div>

                <div className="text-right">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {game?.home_leader_pts_name ?? "-"}
                  </span>
                  <span className="ml-2 text-gray-500 dark:text-zinc-400">
                    {game?.home_leader_pts_val ?? ""}
                  </span>
                </div>
              </div>

              {/* Rebounds */}
              <div className="grid grid-cols-3 items-center">
                <div className="text-left">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {game?.away_leader_reb_name ?? "-"}
                  </span>
                  <span className="ml-2 text-gray-500 dark:text-zinc-400">
                    {game?.away_leader_reb_val ?? ""}
                  </span>
                </div>

                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  Rebounds
                </div>

                <div className="text-right">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {game?.home_leader_reb_name ?? "-"}
                  </span>
                  <span className="ml-2 text-gray-500 dark:text-zinc-400">
                    {game?.home_leader_reb_val ?? ""}
                  </span>
                </div>
              </div>

              {/* Assists */}
              <div className="grid grid-cols-3 items-center">
                <div className="text-left">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {game?.away_leader_ast_name ?? "-"}
                  </span>
                  <span className="ml-2 text-gray-500 dark:text-zinc-400">
                    {game?.away_leader_ast_val ?? ""}
                  </span>
                </div>

                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  Assists
                </div>

                <div className="text-right">
                  <span className="font-semibold text-zinc-900 dark:text-zinc-100">
                    {game?.home_leader_ast_name ?? "-"}
                  </span>
                  <span className="ml-2 text-gray-500 dark:text-zinc-400">
                    {game?.home_leader_ast_val ?? ""}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Team Stats */}
          <div className="rounded-2xl bg-white dark:bg-zinc-900 shadow-sm border border-gray-200 dark:border-zinc-700 p-6">
            <h3 className="text-lg font-bold text-gray-900 dark:text-zinc-100 mb-6 text-center">
              Team Stats
            </h3>

            <div className="space-y-4">
              <div className="grid grid-cols-3 items-center">
                <div className="text-left font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.away_points ?? game?.away_score ?? "-"}
                </div>
                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  Points
                </div>
                <div className="text-right font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.home_points ?? game?.home_score ?? "-"}
                </div>
              </div>

              <div className="grid grid-cols-3 items-center">
                <div className="text-left font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.away_reb ?? "-"}
                </div>
                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  Rebounds
                </div>
                <div className="text-right font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.home_reb ?? "-"}
                </div>
              </div>

              <div className="grid grid-cols-3 items-center">
                <div className="text-left font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.away_ast ?? "-"}
                </div>
                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  Assists
                </div>
                <div className="text-right font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.home_ast ?? "-"}
                </div>
              </div>

              <div className="grid grid-cols-3 items-center">
                <div className="text-left font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.away_fgm ?? "-"} / {game?.away_fga ?? "-"}
                </div>
                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  FGM / FGA
                </div>
                <div className="text-right font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.home_fgm ?? "-"} / {game?.home_fga ?? "-"}
                </div>
              </div>

              <div className="grid grid-cols-3 items-center">
                <div className="text-left font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.away_3pm ?? "-"} / {game?.away_3pa ?? "-"}
                </div>
                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  3PM / 3PA
                </div>
                <div className="text-right font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.home_3pm ?? "-"} / {game?.home_3pa ?? "-"}
                </div>
              </div>

              <div className="grid grid-cols-3 items-center">
                <div className="text-left font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.away_ftm ?? "-"} / {game?.away_fta ?? "-"}
                </div>
                <div className="text-center text-gray-500 dark:text-zinc-400 font-semibold">
                  FTM / FTA
                </div>
                <div className="text-right font-semibold text-zinc-900 dark:text-zinc-100">
                  {game?.home_ftm ?? "-"} / {game?.home_fta ?? "-"}
                </div>
              </div>
            </div>
          </div>
        </div>

        {game && <WinProbabilityGraph game={game} />}
      </div>
    </div>
  );
}
