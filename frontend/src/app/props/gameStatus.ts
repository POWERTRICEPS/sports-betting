export type GamePhase = "live" | "pregame" | "final" | "unknown";

export function classifyGameStatus(status: string | undefined): GamePhase {
  const s = (status ?? "").trim().toLowerCase();
  if (!s) return "unknown";

  if (s.includes("final") || s.includes("game over") || s.includes("f/ot")) {
    return "final";
  }

  if (s.includes("pregame") || s.includes("scheduled")) {
    return "pregame";
  }

  if (
    /\b(am|pm)\b/.test(s) &&
    (s.includes("et") || s.includes("est") || s.includes("pt") || s.includes("ct"))
  ) {
    return "pregame";
  }

  return "live";
}
