"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { ConnectionStatus, PropsSnapshotResponse } from "@/app/types";
import PlayerPropCard from "./PropCard";

const BACKEND_URL = "pj09-sports-betting.onrender.com";
// const BACKEND_URL = "localhost:8000";
const isLocal =
  BACKEND_URL.startsWith("localhost") || BACKEND_URL.startsWith("127.0.0.1");
const WS_URL = isLocal ? `ws://${BACKEND_URL}/ws` : `wss://${BACKEND_URL}/ws`;
const PROPS_API_URL = isLocal
  ? `http://${BACKEND_URL}/api/props`
  : `https://${BACKEND_URL}/api/props`;
const PROPS_TOPIC = "props";

function isPropsSnapshotResponse(payload: unknown): payload is PropsSnapshotResponse {
  if (!payload || typeof payload !== "object") return false;
  const obj = payload as Record<string, unknown>;
  if (!Array.isArray(obj.projections)) return false;
  return obj.projections.every((row) => row && typeof row === "object");
}

export default function PropsPageClient() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const wsRef = useRef<WebSocket | null>(null);

  const [snapshot, setSnapshot] = useState<PropsSnapshotResponse>({
    updated_at: null,
    projections: [],
  });
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const uniqueTeams = useMemo(() => {
    const teams = snapshot.projections.map((p) => p.team_abbr);
    return Array.from(new Set(teams)).sort();
  }, [snapshot.projections]);

  const teamParam = searchParams.get("team");
  const sortParam = searchParams.get("sort");
  const queryParam = searchParams.get("q") ?? "";

  const [selectedTeam, setSelectedTeam] = useState<string>(
    () => (teamParam ? teamParam : "All"),
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
    if (selectedTeam !== "All" && !uniqueTeams.includes(selectedTeam)) {
      setSelectedTeam("All");
    }
  }, [selectedTeam, uniqueTeams]);

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

  useEffect(() => {
    let mounted = true;

    async function fetchInitialProps() {
      setIsLoading(true);
      try {
        const res = await fetch(PROPS_API_URL);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (mounted && isPropsSnapshotResponse(data)) {
          setSnapshot(data);
          setError(null);
        }
      } catch (e) {
        console.error("Failed to fetch initial props snapshot:", e);
        if (mounted) {
          setError("Failed to fetch props snapshot");
          setSnapshot({ updated_at: null, projections: [] });
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    }

    fetchInitialProps();
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    setConnectionStatus("connecting");

    ws.onopen = () => {
      setConnectionStatus("connected");
      setError(null);
      ws.send(JSON.stringify({ action: "subscribe", topic: PROPS_TOPIC }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data && typeof data === "object" && "ok" in data) {
          return;
        }
        if (isPropsSnapshotResponse(data)) {
          setSnapshot(data);
        }
      } catch (e) {
        console.error("Failed to parse props websocket message:", e);
      }
    };

    ws.onerror = (event) => {
      console.error("Props websocket error:", event);
      setConnectionStatus("error");
      setError("WebSocket connection error");
    };

    ws.onclose = () => {
      setConnectionStatus("disconnected");
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "unsubscribe", topic: PROPS_TOPIC }));
      }
      ws.close();
      wsRef.current = null;
    };
  }, []);

  const filteredProps = useMemo(() => {
    let result = [...snapshot.projections];
    const normalizedQuery = debouncedQuery.trim().toLowerCase();

    if (selectedTeam !== "All") {
      result = result.filter((p) => p.team_abbr === selectedTeam);
    }

    if (normalizedQuery) {
      result = result.filter((p) =>
        p.player_name.toLowerCase().includes(normalizedQuery),
      );
    }

    if (selectedCategory !== "All") {
      result.sort((a, b) => {
        if (selectedCategory === "PTS") return b.projected_pts - a.projected_pts;
        if (selectedCategory === "REB") return b.projected_reb - a.projected_reb;
        return b.projected_ast - a.projected_ast;
      });
    }

    return result;
  }, [snapshot.projections, selectedTeam, selectedCategory, debouncedQuery]);

  const clearFilters = () => {
    setSelectedTeam("All");
    setSelectedCategory("All");
    setSearchQuery("");
  };

  const hasActiveFilters =
    selectedTeam !== "All" || selectedCategory !== "All" || searchQuery.trim() !== "";
  const totalProps = snapshot.projections.length;
  const visibleProps = filteredProps.length;
  const trimmedSearchQuery = searchQuery.trim();

  return (
    <main className="min-h-screen bg-zinc-50 dark:bg-zinc-950 p-6 pt-20">
      <div className="mx-auto max-w-7xl">
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
            <label className="font-semibold uppercase text-blue-700 dark:text-blue-400">
              Sort By Category
            </label>
            <div className="flex gap-2">
              {["All", "PTS", "REB", "AST"].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`h-10 rounded-lg px-4 text-sm font-medium transition-colors ${
                    selectedCategory === cat
                      ? "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 ring-1 ring-blue-500"
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
          {isLoading ? (
            <div className="col-span-full py-12 text-center text-zinc-500 dark:text-zinc-400">
              Loading props...
            </div>
          ) : filteredProps.length > 0 ? (
            filteredProps.map((player) => (
              <PlayerPropCard
                key={`${player.game_id}-${player.player_id}`}
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

        <div className="mt-8 text-xs text-zinc-500 dark:text-zinc-400">
          <p>
            Status: {connectionStatus}
            {snapshot.updated_at
              ? ` • Updated ${new Date(snapshot.updated_at).toLocaleTimeString()}`
              : ""}
          </p>
          {error && <p className="mt-1 text-red-500">{error}</p>}
        </div>

      </div>
    </main>
  );
}
