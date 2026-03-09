"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import PlayerPropCard from "./PropCard";
import { mockProps } from "./mock";

export default function PropsPageClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const uniqueTeams = useMemo(() => {
    const teams = mockProps.map((p) => p.team);
    return Array.from(new Set(teams)).sort();
  }, []);

  const teamParam = searchParams.get("team");
  const sortParam = searchParams.get("sort");
  const queryParam = searchParams.get("q") ?? "";

  const [selectedTeam, setSelectedTeam] = useState<string>(() =>
    teamParam && (teamParam === "All" || uniqueTeams.includes(teamParam))
      ? teamParam
      : "All",
  );
  const [selectedCategory, setSelectedCategory] = useState<string>(() =>
    sortParam && ["All", "PTS", "REB", "AST"].includes(sortParam)
      ? sortParam
      : "All",
  );
  const [searchQuery, setSearchQuery] = useState<string>(queryParam);
  const [debouncedQuery, setDebouncedQuery] = useState<string>(queryParam);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 200);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  useEffect(() => {
    const params = new URLSearchParams();
    const trimmedQuery = debouncedQuery.trim();

    if (selectedTeam !== "All") params.set("team", selectedTeam);
    if (selectedCategory !== "All") params.set("sort", selectedCategory);
    if (trimmedQuery) params.set("q", trimmedQuery);

    const nextQuery = params.toString();
    const currentQuery = searchParams.toString();

    if (nextQuery !== currentQuery) {
      router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname, {
        scroll: false,
      });
    }
  }, [debouncedQuery, pathname, router, searchParams, selectedCategory, selectedTeam]);

  const filteredProps = useMemo(() => {
    let result = [...mockProps];
    const normalizedQuery = debouncedQuery.trim().toLowerCase();

    if (selectedTeam !== "All") {
      result = result.filter((p) => p.team === selectedTeam);
    }

    if (normalizedQuery) {
      result = result.filter((p) =>
        p.player.toLowerCase().includes(normalizedQuery),
      );
    }

    if (selectedCategory !== "All") {
      result.sort((a, b) => {
        const key = selectedCategory.toLowerCase() as "pts" | "reb" | "ast";
        return b.projected[key] - a.projected[key];
      });
    }

    return result;
  }, [selectedTeam, selectedCategory, debouncedQuery]);

  const clearFilters = () => {
    setSelectedTeam("All");
    setSelectedCategory("All");
    setSearchQuery("");
  };

  const hasActiveFilters =
    selectedTeam !== "All" || selectedCategory !== "All" || searchQuery.trim() !== "";
  const totalProps = mockProps.length;
  const visibleProps = filteredProps.length;
  const trimmedSearchQuery = searchQuery.trim();

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-zinc-950 p-6 pt-20">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-emerald-600 dark:text-emerald-400">
              Live Player Props
            </h1>
            <p className="mt-1 text-zinc-600 dark:text-zinc-300">
              Check out today&apos;s player props and predictions
            </p>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-4 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-4 shadow-sm md:flex-row md:items-center">
          <div className="flex flex-col gap-1.5">
            <label className="font-semibold uppercase text-neutral-950 dark:text-zinc-100">
              Search Player
            </label>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="First, last, or full name"
              className="h-10 w-full rounded-lg border border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 text-sm font-medium text-zinc-700 dark:text-zinc-200 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 md:w-64"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-semibold uppercase text-neutral-950 dark:text-zinc-100">
              Select Team
            </label>
            <select
              value={selectedTeam}
              onChange={(e) => setSelectedTeam(e.target.value)}
              className="h-10 w-full rounded-lg border border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 text-sm font-medium text-zinc-700 dark:text-zinc-200 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 md:w-48"
            >
              <option value="All">All Teams</option>
              {uniqueTeams.map((team) => (
                <option key={team} value={team}>
                  {team}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="font-semibold uppercase text-emerald-600 dark:text-emerald-400">
              Sort By Category
            </label>
            <div className="flex gap-2">
              {["All", "PTS", "REB", "AST"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`h-10 rounded-lg px-4 text-sm font-medium transition-colors ${
                    selectedCategory === cat
                      ? "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300 ring-1 ring-emerald-500"
                      : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 hover:bg-zinc-200 dark:hover:bg-zinc-700"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {hasActiveFilters && (
            <div className="md:ml-auto md:self-end">
              <button
                onClick={clearFilters}
                className="h-10 rounded-lg px-4 text-sm font-medium text-red-500 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                Clear All
              </button>
            </div>
          )}
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div className="col-span-full text-sm text-zinc-600 dark:text-zinc-300">
            Showing {visibleProps} of {totalProps} players
          </div>
          {filteredProps.length > 0 ? (
            filteredProps.map((player) => (
              <PlayerPropCard
                key={`${player.player}-${player.team}`}
                data={player}
                highlightQuery={debouncedQuery}
              />
            ))
          ) : (
            <div className="col-span-full py-12 text-center text-zinc-500 dark:text-zinc-400">
              {trimmedSearchQuery ? (
                <div className="flex flex-col items-center gap-3">
                  <p>{`No players found for "${trimmedSearchQuery}".`}</p>
                  <button
                    type="button"
                    onClick={() => setSearchQuery("")}
                    className="h-9 rounded-lg px-3 text-sm font-medium text-emerald-700 dark:text-emerald-300 ring-1 ring-emerald-500 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                  >
                    Clear search
                  </button>
                </div>
              ) : (
                "No props found matching your filters."
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
