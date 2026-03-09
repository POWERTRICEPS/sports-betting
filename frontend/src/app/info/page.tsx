export default function InfoPage() {
  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 p-6 pt-20">
      <article className="mx-auto max-w-4xl space-y-8">
        <header className="space-y-2">
          <h1 className="text-3xl font-bold">How to Use This App</h1>
          <p className="text-zinc-600 dark:text-zinc-300">
            This page explains what each page shows, where the numbers come
            from, and practical ways to use the tool.
          </p>
        </header>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6">
          <h2 className="text-2xl font-semibold">Games Page</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>
              Shows active/scheduled NBA games, records, scores, status, and win
              probability for each matchup.
            </li>
            <li>
              Main data source: <code>GET /api/games</code> plus live updates
              from WebSocket topic <code>games</code>.
            </li>
            <li>
              If backend data is unavailable, the UI falls back to local mock
              data so the page still renders.
            </li>
            <li>
              Standings panel is loaded from <code>GET /api/standings</code>.
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6">
          <h2 className="text-2xl font-semibold">Individual Game Page</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>
              Shows team info, score by quarter, game leaders, team stats, and a
              win probability chart for one game.
            </li>
            <li>
              Data source: <code>GET /api/games/stats/{"{"}game_id{"}"}</code> and
              WebSocket topic <code>game:{"{"}game_id{"}"}</code>.
            </li>
            <li>
              Win probability values come from backend probabilities when
              available.
            </li>
            <li>
              If quarter-level data is missing, the chart marks the line as
              sample data.
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6">
          <h2 className="text-2xl font-semibold">Props Page</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>
              Shows player projections for PTS, REB, and AST with search/filter
              tools.
            </li>
            <li>Current source in frontend is local mock projections.</li>
            <li>
              Projection cards also show game context and on-floor indicator to
              help compare players quickly.
            </li>
            <li>These values are projections, not sportsbook lines.</li>
          </ul>
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6">
          <h2 className="text-2xl font-semibold">Ways to Use the Tool</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>
              Start on Games to identify close games, momentum changes, or large
              win probability swings.
            </li>
            <li>
              Open an individual game to inspect leaders and team stats before
              evaluating prop angles.
            </li>
            <li>
              Use Props filters to find players, then compare projected
              PTS/REB/AST against your preferred sportsbook lines.
            </li>
            <li>
              Use this tool as informational support only, not guaranteed betting
              advice.
            </li>
          </ul>
        </section>
      </article>
    </main>
  );
}
