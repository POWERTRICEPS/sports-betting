"use client";

import { useState } from 'react';
import { Game } from '../types';
import Image from 'next/image';
import Link from 'next/link';
import { teamPrimaryColors } from '../resources/colors';

function formatProb(n: number | null) {
  if (n === null || Number.isNaN(n)) return "N/A";
  return `${Math.round(n)}%`;
}

const imgSize = 100;

export default function GameCard({ data }: { data: Game }) {
  const [isHovered, setIsHovered] = useState(false);
  let homePrimary = teamPrimaryColors[data.home_abbreviation] || '#1F2937';
  let awayPrimary = teamPrimaryColors[data.away_abbreviation] || '#1F2937';

  return (
    <Link
      href={`/games/${data.game_id}`}
      className="block border border-gray-300 dark:border-zinc-700 rounded-lg p-6 shadow-md hover:shadow-lg transform transition-all duration-200 hover:scale-105 cursor-pointer"
      style={{
        background: `
          radial-gradient(ellipse 120% 100% at 0% 0%, ${homePrimary}65, transparent 65%),
          radial-gradient(ellipse 120% 100% at 100% 0%, ${awayPrimary}65, transparent 65%)
        `,
        boxShadow: isHovered
          ? '0 0 30px rgba(100, 220, 255, 0.9), inset 0 0 1px rgba(100, 220, 255, 0.3)'
          : 'none'
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Status / Time Remaining */}
      <div className="text-center mb-4">
        <p className="text-sm text-gray-500">{data.status}</p>
      </div>

      {/* Teams and Scores */}
      <div className="flex justify-between items-center mb-4">
        {/* Team 1 */}
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
            {data.home_score}
          </p>
        </div>

        {/* Divider */}
        <div className="px-4 text-gray-300 dark:text-zinc-500 text-2xl">vs</div>

        {/* Team 2 */}
        <div className="flex-1 text-center">
          <Image
            src={`https://a1.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/scoreboard/${data.away_abbreviation}.png&h=456&w=456`}
            alt={`${data.away_team} logo`}
            width={imgSize}
            height={imgSize}
            className="mx-auto"
          />
          <h3 className="font-bold text-lg">{data.away_team}</h3>
          <p className="text-sm text-gray-600 dark:text-zinc-300">
            {data.away_wins}-{data.away_losses}
          </p>
          <p className="text-3xl font-bold text-red-500 dark:text-red-400 mt-2">
            {data.away_score}
          </p>
        </div>
      </div>

      {/* Win Probabilities */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-zinc-700">
        <div className="flex justify-between items-center">
          <span className="text-gray-700 dark:text-zinc-200 font-medium">Win Prob:</span>
          <span className="font-bold text-lg text-green-600 dark:text-emerald-400">
            {formatProb(data.home_win_prob ?? null)} / {formatProb(data.away_win_prob ?? null)}
          </span>
        </div>
      </div>
    </Link>
  );
}
