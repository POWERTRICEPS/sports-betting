"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import type { PlayerProjection } from "@/app/types";
import { teamPrimaryColors, teamSecondaryColors } from "../resources/colors";

function getHeadshotUrl(espnPlayerId: string): string {
  return `https://a.espncdn.com/i/headshots/nba/players/full/${espnPlayerId}.png`;
}

function normalizeTeamAbbr(teamAbbr: string): string {
  const aliases: Record<string, string> = {
    GSW: "GS",
    NYK: "NY",
    SAS: "SA",
    NOP: "NO",
    WAS: "WSH",
    UTA: "UTAH",
  };
  return aliases[teamAbbr] ?? teamAbbr;
}

function HighlightedName({ name, query }: { name: string; query?: string }) {
  const trimmedQuery = query?.trim() ?? "";
  if (!trimmedQuery) {
    return <>{name}</>;
  }

  const lowerName = name.toLowerCase();
  const lowerQuery = trimmedQuery.toLowerCase();
  const start = lowerName.indexOf(lowerQuery);

  if (start === -1) {
    return <>{name}</>;
  }

  const end = start + trimmedQuery.length;
  return (
    <>
      {name.slice(0, start)}
      <span className="rounded bg-emerald-100 px-1 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
        {name.slice(start, end)}
      </span>
      {name.slice(end)}
    </>
  );
}

export default function PlayerPropCard({
  data,
  highlightQuery,
}: {
  data: PlayerProjection;
  highlightQuery?: string;
}) {
  const [imgFailed, setImgFailed] = useState(false);
  const headshotUrl = getHeadshotUrl(data.espn_player_id);
  const colorKey = normalizeTeamAbbr(data.team_abbr);
  const teamPrimary = teamPrimaryColors[colorKey] ?? "#1F2937";
  const teamSecondary = teamSecondaryColors[colorKey] ?? teamPrimary;
  const initials = useMemo(
    () =>
      data.player_name
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() ?? "")
        .join(""),
    [data.player_name],
  );
  return (
    <div
      className="w-full max-w-md rounded-2xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-4 shadow-sm"
      style={{
        background: `
          radial-gradient(ellipse 120% 100% at 0% 0%, ${teamPrimary}65, transparent 65%),
          radial-gradient(ellipse 120% 100% at 100% 0%, ${teamSecondary}65, transparent 65%)
        `,
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {imgFailed ? (
            <div className="flex h-14 w-14 items-center justify-center rounded-full border border-zinc-300 bg-zinc-100 text-xs font-semibold text-zinc-700 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
              {initials || "N/A"}
            </div>
          ) : (
            <Image
              src={headshotUrl}
              alt={data.player_name}
              width={56}
              height={56}
              className="h-14 w-14 rounded-full object-cover border border-zinc-300 dark:border-zinc-700"
              unoptimized
              onError={() => setImgFailed(true)}
            />
          )}
          <div>
            <div className="text-lg font-semibold leading-tight text-zinc-900 dark:text-zinc-100">
              <HighlightedName name={data.player_name} query={highlightQuery} />
            </div>
            <div className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              {data.team_abbr} vs {data.opponent_abbr}
            </div>
          </div>
        </div>
      </div>

      {/* Projected Stats */}
      <div className="mt-4 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 px-4 py-3">
        <div className="mb-3 text-center">
          <div className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Projected Stats
          </div>
          <div className="mt-3 h-px w-full bg-zinc-200 dark:bg-zinc-600" />
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-xs text-zinc-500 dark:text-zinc-400">PTS</div>
            <div className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              {data.projected_pts}
            </div>
          </div>
          <div>
            <div className="text-xs text-zinc-500 dark:text-zinc-400">REB</div>
            <div className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              {data.projected_reb}
            </div>
          </div>
          <div>
            <div className="text-xs text-zinc-500 dark:text-zinc-400">AST</div>
            <div className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              {data.projected_ast}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
