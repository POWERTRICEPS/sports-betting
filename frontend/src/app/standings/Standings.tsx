"use client";

import { useState } from "react";
import Image from "next/image";
import { teamPrimaryColors, teamSecondaryColors } from "../resources/colors";
import { useGameData } from "../GameDataProvider";

//make this a jsx element
function LazyImage({
  src,
  alt,
  width,
  height,
  maxRetries = 3,
}: {
  src: string;
  alt: string;
  width: number;
  height: number;
  maxRetries?: number;
}) {
  const [retryCount, setRetryCount] = useState(0);
  const [key, setKey] = useState(0); // force reload

  const handleError = () => {
    if (retryCount < maxRetries) {
      setRetryCount((prev) => prev + 1);
      setKey((prev) => prev + 1); // change key to force <Image> reload
    }
  };

  return (
    <Image
      key={key}
      src={src}
      alt={alt}
      width={width}
      height={height}
      onError={handleError}
      loading="lazy"
    />
  );
}

export default function Standings() {
  const { standings, standingsLoading } = useGameData();
  const [conference, setConference] = useState<"East" | "West">("East");

  // Determine which list to show based on tab selection
  const currentStandings =
    conference === "East"
      ? standings?.east_standings
      : standings?.west_standings;

  return (
    <div className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6 flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
          NBA Standings
        </h2>

        {/* Conference Toggle */}
        <div className="flex rounded-md bg-zinc-100 dark:bg-zinc-800 p-1">
          <button
            onClick={() => setConference("East")}
            className={`rounded px-3 py-1 text-xs font-medium transition-all ${
              conference === "East"
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-sm"
                : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
            }`}
          >
            East
          </button>
          <button
            onClick={() => setConference("West")}
            className={`rounded px-3 py-1 text-xs font-medium transition-all ${
              conference === "West"
                ? "bg-white dark:bg-zinc-700 text-zinc-900 dark:text-zinc-100 shadow-sm"
                : "text-zinc-500 dark:text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200"
            }`}
          >
            West
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div>
        {standingsLoading ? (
          <div className="flex h-40 items-center justify-center text-sm text-zinc-400 dark:text-zinc-500">
            Loading...
          </div>
        ) : !currentStandings ? (
          <div className="flex h-40 items-center justify-center text-sm text-zinc-400 dark:text-zinc-500">
            No data available
          </div>
        ) : (
          <div className="relative overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-zinc-100 dark:border-zinc-700 text-xs font-medium text-zinc-400 dark:text-zinc-500 uppercase">
                <tr>
                  <th className="pb-2 pl-2">#</th>
                  <th className="pb-2">Team</th>
                  <th className="pb-2 text-right pr-2">Record</th>
                  <th className="pb-2 text-center">L10</th>
                  <th className="pb-2 text-center">Streak</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-50 dark:divide-zinc-700">
                {currentStandings.map((team) => (
                  <tr
                    key={team.team_id}
                    className="transition-colors"
                    style={
                      {
                        "--bg-color": `${teamPrimaryColors[team.team_abbreviation]}20`,
                        background: `radial-gradient(circle at 0% 50%, var(--bg-color), transparent 40%)`,
                      } as React.CSSProperties
                    }
                    onMouseEnter={(e) =>
                      e.currentTarget.style.setProperty(
                        "--bg-color",
                        `${teamSecondaryColors[team.team_abbreviation]}20`,
                      )
                    }
                    onMouseLeave={(e) =>
                      e.currentTarget.style.setProperty(
                        "--bg-color",
                        `${teamPrimaryColors[team.team_abbreviation]}20`,
                      )
                    }
                  >
                    <td className="py-2.5 pl-2 font-medium text-zinc-500 dark:text-zinc-400 w-8">
                      {team.rank}
                    </td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <LazyImage
                          src={`https://a1.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/scoreboard/${team.team_abbreviation}.png&h=456&w=456`}
                          width={20}
                          height={20}
                          alt={`${team.team_city} ${team.team_name} logo`}
                        />
                        <div className="flex flex-col">
                          <span className="font-medium text-zinc-900 dark:text-zinc-100">
                            {team.team_city}
                          </span>
                          <span className="text-xs text-zinc-400 dark:text-zinc-500">
                            {team.team_name}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="py-2.5 text-right pr-2 font-medium text-zinc-700 dark:text-zinc-300">
                      {team.record}
                    </td>
                    <td className="py-2.5 text-center text-xs text-zinc-600 dark:text-zinc-400">
                      {team.team_L10}
                    </td>
                    <td
                      className={`py-2.5 text-center text-xs font-medium ${
                        team.curr_streak.includes("W")
                          ? "text-green-600 dark:text-emerald-400"
                          : "text-red-600 dark:text-red-400"
                      }`}
                    >
                      {team.curr_streak.replaceAll(" ", "")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
