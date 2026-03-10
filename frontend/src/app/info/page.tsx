export default function InfoPage() {
  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 px-6 pt-24 pb-16">
      <article className="mx-auto max-w-4xl">
        <header className="relative overflow-hidden rounded-2xl border border-zinc-200 bg-white px-6 py-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 sm:px-8">
          <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-cyan-200/50 blur-3xl dark:bg-cyan-900/40" />
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-400">
            Help Guide
          </p>
          <h1 className="mt-2 text-4xl font-bold tracking-tight">How to Use This App</h1>
          <p className="mt-3 max-w-2xl text-zinc-600 dark:text-zinc-300">
            This page gives you a quick, practical path to using Games,
            individual game views, and Props together.
          </p>
        </header>

        <section className="mt-8 grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Step 1
            </p>
            <h2 className="mt-2 text-lg font-semibold">Scan Games</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
              Start with the Games page to spot matchups that look close or
              volatile.
            </p>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Step 2
            </p>
            <h2 className="mt-2 text-lg font-semibold">Open Details</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
              Click any game card to review quarter scoring, team stats, and
              leaders.
            </p>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Step 3
            </p>
            <h2 className="mt-2 text-lg font-semibold">Compare Props</h2>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-300">
              Use the Props page filters to narrow players and compare
              projections.
            </p>
          </div>
        </section>

        <section className="mt-8 space-y-8">
          <div className="border-l-2 border-cyan-600 pl-5 dark:border-cyan-500">
            <h3 className="text-2xl font-semibold">Games Page</h3>
            <p className="mt-2 text-zinc-700 dark:text-zinc-300">
              You get a fast snapshot of today&apos;s matchups, including current
              score, status, records, and win probability. Every game card is
              clickable, so you can jump straight into the detailed game view.
              You can also pin key games to keep your priority matchups easy to
              find.
            </p>
          </div>

          <div className="border-l-2 border-cyan-600 pl-5 dark:border-cyan-500">
            <h3 className="text-2xl font-semibold">Individual Game Page</h3>
            <p className="mt-2 text-zinc-700 dark:text-zinc-300">
              This page gives the full context: quarter-by-quarter scoring, team
              comparison stats, top performers, and live probability movement.
              Use it when you want to understand game flow instead of relying on
              final score alone.
            </p>
          </div>

          <div className="border-l-2 border-cyan-600 pl-5 dark:border-cyan-500">
            <h3 className="text-2xl font-semibold">Props Page</h3>
            <p className="mt-2 text-zinc-700 dark:text-zinc-300">
              The Props page lets you browse projections for points, rebounds,
              and assists. Search and filters help you focus on specific
              players, teams, or stat types so you can compare options quickly
              with game context in view.
            </p>
          </div>
        </section>

        <section className="mt-10 rounded-2xl border border-amber-200 bg-amber-50/70 px-6 py-7 text-center text-sm leading-7 text-zinc-700 dark:border-amber-900/60 dark:bg-amber-950/20 dark:text-zinc-300">
          <p>
            This app is for informational and educational purposes only. Stats,
            win probabilities, and player projections are estimates and may be
            delayed, incomplete, or inaccurate. Nothing shown in this app is
            financial, betting, or legal advice, and no outcome is guaranteed.
          </p>
          <p className="mt-4">
            Users are responsible for verifying all information with official
            sources and for following the laws and age requirements in their
            location. This project is not a sportsbook and does not accept
            wagers.
          </p>
          <p className="mt-4">
            If gambling is causing harm, help is available 24/7 in the U.S. at{" "}
            <a
              href="tel:18004262537"
              className="font-semibold text-cyan-700 hover:underline dark:text-cyan-400"
            >
              1-800-GAMBLER (1-800-426-2537)
            </a>{" "}
            or by visiting{" "}
            <a
              href="https://www.1800gambler.net"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold text-cyan-700 hover:underline dark:text-cyan-400"
            >
              1800gambler.net
            </a>
            .
          </p>
        </section>
      </article>
    </main>
  );
}
