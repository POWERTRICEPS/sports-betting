"use client";

type GameListStateProps = {
  message: string;
};

type GameListErrorProps = {
  message: string;
  onRetry?: () => void;
};

type GameDetailErrorProps = {
  message: string;
  onRetry: () => void;
};

export function GameCardsSkeleton({ count = 6 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={`game-skeleton-${i}`}
          data-testid="game-card-skeleton"
          className="h-[300px] animate-pulse rounded-lg border border-zinc-200 bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800"
        />
      ))}
    </>
  );
}

export function GamesListEmptyState({ message }: GameListStateProps) {
  return (
    <div className="col-span-full rounded-lg border border-dashed border-zinc-300 bg-zinc-100/70 p-8 text-center text-zinc-600 dark:border-zinc-700 dark:bg-zinc-900/60 dark:text-zinc-300">
      {message}
    </div>
  );
}

export function GamesListErrorState({ message, onRetry }: GameListErrorProps) {
  return (
    <div className="col-span-full rounded-lg border border-red-200 bg-red-50 p-8 text-center dark:border-red-900/70 dark:bg-red-950/30">
      <p className="text-red-700 dark:text-red-300">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function GameDetailLoadingState() {
  return (
    <div
      data-testid="game-detail-loading"
      className="mx-auto max-w-5xl animate-pulse rounded-2xl border border-zinc-200 bg-zinc-100 p-8 dark:border-zinc-700 dark:bg-zinc-900"
    >
      <div className="h-8 w-40 rounded bg-zinc-200 dark:bg-zinc-800" />
      <div className="mt-6 h-56 rounded bg-zinc-200 dark:bg-zinc-800" />
      <div className="mt-6 h-40 rounded bg-zinc-200 dark:bg-zinc-800" />
    </div>
  );
}

export function GameDetailErrorState({ message, onRetry }: GameDetailErrorProps) {
  return (
    <div
      data-testid="game-detail-error"
      className="mx-auto max-w-3xl rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-900/70 dark:bg-red-950/30"
    >
      <p className="text-red-700 dark:text-red-300">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
      >
        Retry
      </button>
    </div>
  );
}
