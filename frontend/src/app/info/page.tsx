export default function InfoPage() {
  return (
    <main className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100 p-6 pt-20">
      <article className="mx-auto max-w-4xl space-y-8">
        <header className="space-y-2">
          <h1 className="text-3xl font-bold">How to Use This App</h1>
          <p className="text-zinc-600 dark:text-zinc-300">
            This guide explains what you can do on each page and how the
            numbers can help you make better decisions.
          </p>
        </header>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6">
          <h2 className="text-2xl font-semibold">Ways to Use the Tool</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>
              Start on Games to find matchups that look interesting.
            </li>
            <li>
              Open one game for deeper context before making decisions.
            </li>
            <li>
              Use Props to compare player projections and shortlist targets.
            </li>
            <li>
              Treat this app as decision support, not guaranteed advice.
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6">
          <h2 className="text-2xl font-semibold">Games Page</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>
              See today&apos;s matchups at a glance, including score, game status,
              team records, and each team&apos;s chance to win.
            </li>
            <li>
              Each game card is clickable. Click any card to open that game&apos;s
              full details page.
            </li>
            <li>
              You can also pin games you care about so they stay easy to find.
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6">
          <h2 className="text-2xl font-semibold">Individual Game Page</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>
              Get a deeper look at one matchup with quarter-by-quarter scoring,
              team stats, game leaders, and a live win-probability view.
            </li>
            <li>
              Use this page when you want context, not just the final score.
            </li>
            <li>
              It helps answer questions like: Which team is controlling the
              game? Who is producing the most? Is the game trending one way?
            </li>
            <li>
              If some stats are missing during a game, values may update as new
              information comes in.
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6">
          <h2 className="text-2xl font-semibold">Props Page</h2>
          <ul className="mt-3 list-disc pl-5 space-y-2 text-zinc-700 dark:text-zinc-300">
            <li>
              Browse player stat projections for points, rebounds, and assists.
            </li>
            <li>
              Use search and filters to narrow down to specific teams, players,
              or stat categories.
            </li>
            <li>
              Player cards include game context so you can compare options more
              quickly.
            </li>
            <li>
              These values are projections, so they are best used as a guide
              alongside your own judgment.
            </li>
          </ul>
        </section>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-6 text-sm leading-7 text-zinc-600 dark:text-zinc-300 text-center">
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
