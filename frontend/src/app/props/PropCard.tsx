"use client";

import { useMemo, useState } from "react";
import Image from "next/image";

type Prop = {
  espnPlayerId: string;
  player: string;
  team: string;
  opponent: string;

  projected: {
    pts: number;
    reb: number;
    ast: number;
  };

  onFloor: boolean;

  game: {
    teamScore: number;
    oppScore: number;
    quarter: string;
    clock: string;
  };
};

function getHeadshotUrl(espnPlayerId: string): string {
  return `https://a.espncdn.com/i/headshots/nba/players/full/${espnPlayerId}.png`;
}

function FloorIndicator({ on }: { on: boolean }) {
  return (
    <div className="flex items-center gap-2 text-xs font-medium">
      <span
        className={`h-2.5 w-2.5 rounded-full ${
          on ? "bg-emerald-500" : "bg-zinc-300 dark:bg-zinc-600"
        }`}
      />
      <span className={on ? "text-emerald-600 dark:text-emerald-400" : "text-zinc-500 dark:text-zinc-400"}>
        {on ? "On floor" : "Off floor"}
      </span>
    </div>
  );
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
  data: Prop;
  highlightQuery?: string;
}) {
  const [imgFailed, setImgFailed] = useState(false);
  const headshotUrl = getHeadshotUrl(data.espnPlayerId);
  const initials = useMemo(
    () =>
      data.player
        .split(" ")
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase() ?? "")
        .join(""),
    [data.player],
  );
  return (
    <div className="w-full max-w-md rounded-2xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-4 shadow-sm">
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
              alt={data.player}
              width={56}
              height={56}
              className="h-14 w-14 rounded-full object-cover border border-zinc-300 dark:border-zinc-700"
              unoptimized
              onError={() => setImgFailed(true)}
            />
          )}
          <div>
            <div className="text-lg font-semibold leading-tight text-zinc-900 dark:text-zinc-100">
              <HighlightedName name={data.player} query={highlightQuery} />
            </div>
            <div className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              {data.team} vs {data.opponent}
            </div>
          </div>
        </div>

        <FloorIndicator on={data.onFloor} />
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
              {data.projected.pts}
            </div>
          </div>
          <div>
            <div className="text-xs text-zinc-500 dark:text-zinc-400">REB</div>
            <div className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              {data.projected.reb}
            </div>
          </div>
          <div>
            <div className="text-xs text-zinc-500 dark:text-zinc-400">AST</div>
            <div className="mt-1 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              {data.projected.ast}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Game Info */}
      <div className="mt-4 flex items-center justify-between text-xs text-zinc-500 dark:text-zinc-400">
        <span>
          <span className="font-medium text-zinc-600 dark:text-zinc-300">Game Score:</span>{" "}
          {data.game.teamScore}–{data.game.oppScore}
        </span>

        <span>
          {data.game.quarter} • {data.game.clock}
        </span>
      </div>
    </div>
  );
}
