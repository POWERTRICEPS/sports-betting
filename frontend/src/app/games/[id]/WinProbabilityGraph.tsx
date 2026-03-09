'use client';

import { Game } from '@/app/types';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ReferenceLine,
    ResponsiveContainer,
} from 'recharts';

interface WinProbabilityGraphProps {
    game: Game;
}

interface DataPoint {
    index: number;
    home: number;
    away: number;
    clock: string;
}

/**
 * Extract a period identifier from the game-clock string for tick labeling.
 * ESPN clock strings look like "7:07 - 3rd", "Halftime", "Final", etc.
 */
function extractPeriod(clock: string): string {
    if (!clock) return '';
    if (/halftime/i.test(clock)) return 'HT';
    if (/final/i.test(clock)) return 'F';
    if (/end of/i.test(clock)) {
        if (clock.includes('1st')) return 'Q1';
        if (clock.includes('2nd')) return 'Q2';
        if (clock.includes('3rd')) return 'Q3';
        if (clock.includes('4th')) return 'Q4';
    }
    if (/1st/.test(clock)) return 'Q1';
    if (/2nd/.test(clock)) return 'Q2';
    if (/3rd/.test(clock)) return 'Q3';
    if (/4th/.test(clock)) return 'Q4';
    if (/overtime|ot/i.test(clock)) return 'OT';
    if (/pregame|scheduled/i.test(clock)) return 'Pre';
    if (/est|et\b|pm|am/i.test(clock)) return 'Pre';
    return '';
}

/**
 * Build the chart data array directly from backend probability snapshots.
 * No frontend estimation — every point is an ML-produced probability.
 */
function buildData(game: Game): DataPoint[] {
    const history = game.probability_history;

    if (!history || history.length === 0) {
        // No history yet — show just the current ML probability as a single point
        const home = game.home_win_prob;
        const away = game.away_win_prob;
        if (home != null && away != null) {
            return [{ index: 0, home, away, clock: game.status }];
        }
        return [];
    }

    return history.map((snap, i) => ({
        index: i,
        home: snap.home_win_prob,
        away: snap.away_win_prob,
        clock: snap.clock,
    }));
}

/**
 * Compute tick positions at period transitions so the X-axis shows
 * meaningful labels (Q1, Q2, HT, Q3, Q4, F) instead of every data point.
 */
function computeTicks(data: DataPoint[]): {
    positions: number[];
    labels: Record<number, string>;
} {
    const positions: number[] = [];
    const labels: Record<number, string> = {};

    if (data.length === 0) return { positions, labels };

    // Single data point — just label it
    if (data.length === 1) {
        positions.push(0);
        labels[0] = extractPeriod(data[0].clock) || data[0].clock;
        return { positions, labels };
    }

    let prevPeriod = '';
    for (let i = 0; i < data.length; i++) {
        const period = extractPeriod(data[i].clock);
        if (period && period !== prevPeriod) {
            positions.push(i);
            labels[i] = period;
            prevPeriod = period;
        }
    }

    // Always include the last point so the axis stretches to the end
    const lastIdx = data.length - 1;
    if (!positions.includes(lastIdx)) {
        const lastPeriod = extractPeriod(data[lastIdx].clock);
        if (lastPeriod) {
            positions.push(lastIdx);
            labels[lastIdx] = lastPeriod;
        }
    }

    return { positions, labels };
}

/* Custom tooltip for the chart */
function ProbTooltip({ active, payload }: any) {
    if (!active || !payload?.length) return null;
    const home = payload.find((p: any) => p.dataKey === 'home');
    const away = payload.find((p: any) => p.dataKey === 'away');
    const clock: string = payload[0]?.payload?.clock || '';
    return (
        <div className="rounded-lg border border-gray-200 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 shadow-md text-xs">
            <div className="font-semibold text-gray-700 dark:text-zinc-200 mb-1">
                {clock}
            </div>
            {home && (
                <div className="flex items-center gap-1.5">
                    <span
                        className="inline-block h-2 w-2 rounded-full"
                        style={{ background: '#16a34a' }}
                    />
                    <span className="text-gray-600 dark:text-zinc-400">
                        Home:
                    </span>
                    <span className="font-bold text-gray-900 dark:text-zinc-100">
                        {home.value.toFixed(1)}%
                    </span>
                </div>
            )}
            {away && (
                <div className="flex items-center gap-1.5">
                    <span
                        className="inline-block h-2 w-2 rounded-full"
                        style={{ background: '#ef4444' }}
                    />
                    <span className="text-gray-600 dark:text-zinc-400">
                        Away:
                    </span>
                    <span className="font-bold text-gray-900 dark:text-zinc-100">
                        {away.value.toFixed(1)}%
                    </span>
                </div>
            )}
        </div>
    );
}

export default function WinProbabilityGraph({
    game,
}: WinProbabilityGraphProps) {
    if (!game) return null;

    const data = buildData(game);

    // Nothing to show yet
    if (data.length === 0) {
        return (
            <div className="mt-10 mx-auto max-w-4xl">
                <h4 className="text-center text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-1">
                    Win Probability
                </h4>
                <p className="text-center text-sm text-gray-500 dark:text-zinc-400 mt-4">
                    Probability data is not available yet.
                </p>
            </div>
        );
    }

    const homeProb = game.home_win_prob ?? 50;
    const awayProb = game.away_win_prob ?? 50;
    const homeFavored = homeProb >= awayProb;

    const { positions: tickPositions, labels: tickLabels } =
        computeTicks(data);

    return (
        <div className="mt-10 mx-auto max-w-4xl">
            <h4 className="text-center text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-1">
                Win Probability
            </h4>
            <p className="text-center text-xs text-gray-500 dark:text-zinc-400 mb-4">
                {game.away_team} vs {game.home_team}
            </p>

            {/* Chart */}
            <div className="w-full h-72 sm:h-80">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                        data={data}
                        margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
                    >
                        <defs>
                            <linearGradient
                                id="gradHome"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="5%"
                                    stopColor="#16a34a"
                                    stopOpacity={0.3}
                                />
                                <stop
                                    offset="95%"
                                    stopColor="#16a34a"
                                    stopOpacity={0.02}
                                />
                            </linearGradient>
                            <linearGradient
                                id="gradAway"
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="1"
                            >
                                <stop
                                    offset="5%"
                                    stopColor="#ef4444"
                                    stopOpacity={0.3}
                                />
                                <stop
                                    offset="95%"
                                    stopColor="#ef4444"
                                    stopOpacity={0.02}
                                />
                            </linearGradient>
                        </defs>

                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="#e5e7eb"
                        />

                        <XAxis
                            dataKey="index"
                            type="number"
                            domain={[0, data.length - 1]}
                            ticks={tickPositions}
                            tickFormatter={(value: number) =>
                                tickLabels[value] || ''
                            }
                            tick={{ fontSize: 12, fill: '#6b7280' }}
                            axisLine={{ stroke: '#d1d5db' }}
                            tickLine={false}
                        />
                        <YAxis
                            domain={[0, 100]}
                            ticks={[0, 25, 50, 75, 100]}
                            tick={{ fontSize: 11, fill: '#9ca3af' }}
                            axisLine={false}
                            tickLine={false}
                            tickFormatter={(v: number) => `${v}%`}
                        />

                        <ReferenceLine
                            y={50}
                            stroke="#9ca3af"
                            strokeDasharray="4 4"
                            strokeWidth={1}
                        />

                        <Tooltip content={<ProbTooltip />} />

                        <Area
                            type="monotone"
                            dataKey="home"
                            name="Home"
                            stroke="#16a34a"
                            strokeWidth={2}
                            fill="url(#gradHome)"
                            dot={false}
                            activeDot={{
                                r: 4,
                                fill: '#16a34a',
                                stroke: '#fff',
                                strokeWidth: 2,
                            }}
                        />
                        <Area
                            type="monotone"
                            dataKey="away"
                            name="Away"
                            stroke="#ef4444"
                            strokeWidth={2}
                            fill="url(#gradAway)"
                            dot={false}
                            activeDot={{
                                r: 4,
                                fill: '#ef4444',
                                stroke: '#fff',
                                strokeWidth: 2,
                            }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Legend + current probability cards */}
            <div className="grid grid-cols-2 gap-4 mt-6">
                <div
                    className={`rounded-xl border p-4 text-center transition-all ${
                        !homeFavored
                            ? 'border-green-200 dark:border-emerald-700 bg-green-50 dark:bg-emerald-900/30'
                            : 'border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800'
                    }`}
                >
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
                        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-zinc-400">
                            {game.away_team}
                        </span>
                    </div>
                    <div
                        className={`text-3xl font-black ${!homeFavored ? 'text-green-600 dark:text-emerald-400' : 'text-gray-700 dark:text-zinc-200'}`}
                    >
                        {awayProb.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 dark:text-zinc-400 mt-1">
                        {!homeFavored ? 'Favored' : 'Underdog'}
                    </div>
                </div>

                <div
                    className={`rounded-xl border p-4 text-center transition-all ${
                        homeFavored
                            ? 'border-green-200 dark:border-emerald-700 bg-green-50 dark:bg-emerald-900/30'
                            : 'border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800'
                    }`}
                >
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-600" />
                        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-zinc-400">
                            {game.home_team}
                        </span>
                    </div>
                    <div
                        className={`text-3xl font-black ${homeFavored ? 'text-green-600 dark:text-emerald-400' : 'text-gray-700 dark:text-zinc-200'}`}
                    >
                        {homeProb.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 dark:text-zinc-400 mt-1">
                        {homeFavored ? 'Favored' : 'Underdog'}
                    </div>
                </div>
            </div>
        </div>
    );
}
