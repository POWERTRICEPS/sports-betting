"use client";

import { useState } from "react";
import { Game } from "../types";
import Image from "next/image";
import Link from "next/link";
import { teamPrimaryColors } from "../resources/colors";

function formatProb(n: number | null) {
  if (n === null || Number.isNaN(n)) return "N/A";
  return `${Math.round(n)}%`;
}

const imgSize = 100;

type GameCardProps = {
  data: Game;
  isPinned: boolean;
  onTogglePin: (gameId: string) => void;
  disableNavigation?: boolean;
  disabledReason?: string;
};

export default function GameCard({
  data,
  isPinned,
  onTogglePin,
  disableNavigation = false,
  disabledReason,
}: GameCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [showDisabledModal, setShowDisabledModal] = useState(false);

  const homePrimary =
    teamPrimaryColors[data.home_abbreviation] ?? "#1F2937";
  const awayPrimary =
    teamPrimaryColors[data.away_abbreviation] ?? "#1F2937";

  return (
    <>
    <Link
      href={disableNavigation ? "#" : `/games/${data.game_id}`}
      aria-disabled={disableNavigation}
      onClick={(e) => {
        if (disableNavigation) {
          e.preventDefault();
          setShowDisabledModal(true);
        }
      }}
      className={`relative block border border-gray-300 dark:border-zinc-700 rounded-lg p-6 shadow-md transform transition-all duration-200 ${
        disableNavigation
          ? "cursor-pointer opacity-90"
          : "hover:shadow-lg hover:scale-105 cursor-pointer"
      }`}
      style={{
        background: `
          radial-gradient(ellipse 120% 100% at 0% 0%, ${awayPrimary}65, transparent 65%),
          radial-gradient(ellipse 120% 100% at 100% 0%, ${homePrimary}65, transparent 65%)
        `,
        ...(!disableNavigation && isHovered && {
          boxShadow:
            "0 0 30px rgba(100, 220, 255, 0.9), inset 0 0 1px rgba(100, 220, 255, 0.3)",
        }),
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <button
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onTogglePin(data.game_id);
        }}
        className={`
          absolute top-3 right-3 z-10
          p-2 rounded-full transition-all duration-200 active:scale-90
          ${
            isPinned
              ? "bg-yellow-400 text-black shadow-md"
              : "bg-white/70 dark:bg-zinc-800/70 text-gray-600 hover:bg-gray-200 dark:hover:bg-zinc-700"
          }
        `}
      >
        📌
      </button>

      {/* Status */}
      <div className="text-center mb-4">
        <p className="text-sm text-gray-500">{data.status}</p>
      </div>

      {/* Teams and Scores */}
      <div className="flex justify-between items-center mb-4">
        {/* Away Team */}
        <div className="flex-1 text-center">
          <Image
            src={`https://a1.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/scoreboard/${data.away_abbreviation}.png&h=456&w=456`}
            alt={`${data.away_team} logo`}
            width={imgSize}
            height={imgSize}
            className="mx-auto"
            loading="lazy"
          />
          <h3 className="font-bold text-lg">{data.away_team}</h3>
          <p className="text-sm text-gray-600 dark:text-zinc-300">
            {data.away_wins}-{data.away_losses}
          </p>
          <p className="text-3xl font-bold text-red-500 dark:text-red-400 mt-2">
            {data.away_score ?? "-"}
          </p>
        </div>

        {/* Divider */}
        <div className="px-4 text-gray-300 dark:text-zinc-500 text-2xl">
          @
        </div>

        {/* Home Team */}
        <div className="flex-1 text-center">
          <div className="flex-1 justify-center mb-2">
            <Image
              src={`https://a1.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/scoreboard/${data.home_abbreviation}.png&h=456&w=456`}
              alt={`${data.home_team} logo`}
              width={imgSize}
              height={imgSize}
              className="mx-auto"
            />
          </div>
          <h3 className="font-bold text-lg">{data.home_team}</h3>
          <p className="text-sm text-gray-600 dark:text-zinc-300">
            {data.home_wins}-{data.home_losses}
          </p>
          <p className="text-3xl font-bold text-blue-500 dark:text-blue-400 mt-2">
            {data.home_score ?? "-"}
          </p>
        </div>
      </div>

      {/* Win Probability */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-zinc-700">
        <div className="flex justify-between items-center">
          <span className="text-gray-700 dark:text-zinc-200 font-medium">Win Prob:</span>
          <span className="font-bold text-lg text-green-600 dark:text-emerald-400">
            {formatProb(data.away_win_prob ?? null)} / {formatProb(data.home_win_prob ?? null)}
          </span>
        </div>
      </div>
    </Link>
    {showDisabledModal ? (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
        onClick={() => setShowDisabledModal(false)}
      >
        <div
          role="dialog"
          aria-modal="true"
          className="w-full max-w-md rounded-xl border border-zinc-300 bg-white p-6 shadow-xl dark:border-zinc-700 dark:bg-zinc-900"
          onClick={(e) => e.stopPropagation()}
        >
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            Game Details Unavailable
          </h3>
          <p className="mt-3 text-sm text-zinc-600 dark:text-zinc-300">
            {disabledReason ?? "Details available on game day."}
          </p>
          <div className="mt-5 flex justify-end">
            <button
              type="button"
              onClick={() => setShowDisabledModal(false)}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    ) : null}
    </>
  );
}
