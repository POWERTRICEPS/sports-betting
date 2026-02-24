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

/** logistic estimate: maps score differential + time remaining to a win probability. */
function estimateProb(
    homeCumulative: number,
    awayCumulative: number,
    quartersLeft: number,
    homeWinPct: number,
): number {
    const diff = homeCumulative - awayCumulative;
    // As fewer quarters remain, the score diff matters more
    const timeFactor = 1 + (4 - quartersLeft) * 0.6;
    const k = 0.12 * timeFactor;
    // Blend with pregame expectation early, fade it out as game progresses
    const pregameWeight = quartersLeft / 4;
    const logistic = 1 / (1 + Math.exp(-k * diff));
    const blended = pregameWeight * homeWinPct + (1 - pregameWeight) * logistic;
    return Math.max(0, Math.min(100, blended * 100));
}

interface DataPoint {
    label: string;
    home: number;
    away: number;
}


function generateMockQuarters(game: Game) {
    // Simple deterministic seed from game_id
    let seed = 0;
    const id = game.game_id ?? 'default';
    for (let i = 0; i < id.length; i++) {
        seed = ((seed << 5) - seed + id.charCodeAt(i)) | 0;
    }
    const rand = () => {
        seed = (seed * 16807 + 0) % 2147483647;
        return (seed & 0x7fffffff) / 2147483647;
    };

    // Generate plausible quarter scores (20-35 per quarter per team)
    const mockQ = () => Math.floor(rand() * 16) + 20;
    return {
        home_q1: mockQ(), away_q1: mockQ(),
        home_q2: mockQ(), away_q2: mockQ(),
        home_q3: mockQ(), away_q3: mockQ(),
        home_q4: mockQ(), away_q4: mockQ(),
    };
}

/** Returns true when all quarter data is null / missing. */
function hasNoQuarterData(game: Game): boolean {
    return (
        game.home_q1 == null &&
        game.home_q2 == null &&
        game.home_q3 == null &&
        game.home_q4 == null
    );
}

function buildDataPoints(game: Game): { points: DataPoint[]; isMock: boolean } {
    const points: DataPoint[] = [];

    const useMock = hasNoQuarterData(game);
    const mock = useMock ? generateMockQuarters(game) : null;

    const homeWinPct =
        game.home_wins + game.home_losses > 0
            ? game.home_wins / (game.home_wins + game.home_losses)
            : 0.5;

    // Pregame estimate based on records (with slight home‑court bump)
    const pregameHome = Math.max(0, Math.min(100, homeWinPct * 100 + 3));
    points.push({ label: 'Pre', home: pregameHome, away: 100 - pregameHome });

    // Quarter-by-quarter cumulative scores — use real data or mock fallback
    const quarters: { key: string; hq: number | null; aq: number | null }[] = [
        { key: 'Q1', hq: mock?.home_q1 ?? game.home_q1, aq: mock?.away_q1 ?? game.away_q1 },
        { key: 'Q2', hq: mock?.home_q2 ?? game.home_q2, aq: mock?.away_q2 ?? game.away_q2 },
        { key: 'Q3', hq: mock?.home_q3 ?? game.home_q3, aq: mock?.away_q3 ?? game.away_q3 },
        { key: 'Q4', hq: mock?.home_q4 ?? game.home_q4, aq: mock?.away_q4 ?? game.away_q4 },
    ];

    let homeCum = 0;
    let awayCum = 0;

    for (let i = 0; i < quarters.length; i++) {
        const q = quarters[i];
        if (q.hq == null || q.aq == null) break; // quarter hasn't been played yet
        homeCum += q.hq;
        awayCum += q.aq;
        const quartersLeft = 4 - (i + 1);
        const homeP = estimateProb(homeCum, awayCum, quartersLeft, homeWinPct);
        points.push({ label: q.key, home: homeP, away: 100 - homeP });
    }

    // Current actual probability from ML model (if available and game is in progress / final)
    const homeProb = game.home_win_prob;
    const awayProb = game.away_win_prob;
    if (homeProb != null && awayProb != null) {
        const lastLabel = points[points.length - 1]?.label;
        const isLive =
            game.status !== 'Final' &&
            !game.status.includes('EST') &&
            game.status !== 'Pregame' &&
            game.status !== 'Scheduled';
        const nowLabel = game.status === 'Final' ? 'Final' : isLive ? 'Now' : null;

        if (nowLabel && nowLabel !== lastLabel) {
            points.push({ label: nowLabel, home: homeProb, away: awayProb });
        } else if (points.length > 0) {
            points[points.length - 1] = {
                ...points[points.length - 1],
                home: homeProb,
                away: awayProb,
            };
        }
    }

    return { points, isMock: useMock };
}

/* Custom tooltip for the chart */
function ProbTooltip({ active, payload, label }: any) {
    if (!active || !payload?.length) return null;
    const home = payload.find((p: any) => p.dataKey === 'home');
    const away = payload.find((p: any) => p.dataKey === 'away');
    return (
        <div className="rounded-lg border border-gray-200 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 shadow-md text-xs">
            <div className="font-semibold text-gray-700 dark:text-zinc-200 mb-1">{label}</div>
            {home && (
                <div className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-full" style={{ background: '#16a34a' }} />
                    <span className="text-gray-600 dark:text-zinc-400">Home:</span>
                    <span className="font-bold text-gray-900 dark:text-zinc-100">{home.value.toFixed(1)}%</span>
                </div>
            )}
            {away && (
                <div className="flex items-center gap-1.5">
                    <span className="inline-block h-2 w-2 rounded-full" style={{ background: '#ef4444' }} />
                    <span className="text-gray-600 dark:text-zinc-400">Away:</span>
                    <span className="font-bold text-gray-900 dark:text-zinc-100">{away.value.toFixed(1)}%</span>
                </div>
            )}
        </div>
    );
}

export default function WinProbabilityGraph({ game }: WinProbabilityGraphProps) {
    if (!game) return null;

    const { points: data, isMock } = buildDataPoints(game);

    const homeProb = game.home_win_prob ?? 50;
    const awayProb = game.away_win_prob ?? 50;
    const homeFavored = homeProb >= awayProb;

    return (
        <div className="mt-10 mx-auto max-w-4xl">
            <h4 className="text-center text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-1">
                Win Probability
            </h4>
            <p className="text-center text-xs text-gray-500 dark:text-zinc-400 mb-4">
                {game.away_team} vs {game.home_team}
            </p>
            {isMock && (
                <div className="text-center mb-4">
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 px-3 py-1 text-xs font-medium text-amber-700 dark:text-amber-300">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                        </svg>
                        Sample data — quarter scores not yet available
                    </span>
                </div>
            )}

            {/* Chart */}
            <div className="w-full h-72 sm:h-80">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                        <defs>
                            <linearGradient id="gradHome" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#16a34a" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#16a34a" stopOpacity={0.02} />
                            </linearGradient>
                            <linearGradient id="gradAway" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

                        <XAxis
                            dataKey="label"
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
                            tickFormatter={(v) => `${v}%`}
                        />

                        <ReferenceLine y={50} stroke="#9ca3af" strokeDasharray="4 4" strokeWidth={1} />

                        <Tooltip content={<ProbTooltip />} />

                        <Area
                            type="monotone"
                            dataKey="home"
                            name="Home"
                            stroke="#16a34a"
                            strokeWidth={2.5}
                            fill="url(#gradHome)"
                            dot={{ r: 4, fill: '#16a34a', strokeWidth: 0 }}
                            activeDot={{ r: 6, fill: '#16a34a', stroke: '#fff', strokeWidth: 2 }}
                        />
                        <Area
                            type="monotone"
                            dataKey="away"
                            name="Away"
                            stroke="#ef4444"
                            strokeWidth={2.5}
                            fill="url(#gradAway)"
                            dot={{ r: 4, fill: '#ef4444', strokeWidth: 0 }}
                            activeDot={{ r: 6, fill: '#ef4444', stroke: '#fff', strokeWidth: 2 }}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Legend + current probability cards */}
            <div className="grid grid-cols-2 gap-4 mt-6">
                <div className={`rounded-xl border p-4 text-center transition-all ${
                    !homeFavored
                        ? 'border-green-200 dark:border-emerald-700 bg-green-50 dark:bg-emerald-900/30'
                        : 'border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800'
                }`}>
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
                        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-zinc-400">
                            {game.away_team}
                        </span>
                    </div>
                    <div className={`text-3xl font-black ${!homeFavored ? 'text-green-600 dark:text-emerald-400' : 'text-gray-700 dark:text-zinc-200'}`}>
                        {awayProb.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500 dark:text-zinc-400 mt-1">
                        {!homeFavored ? 'Favored' : 'Underdog'}
                    </div>
                </div>

                <div className={`rounded-xl border p-4 text-center transition-all ${
                    homeFavored
                        ? 'border-green-200 dark:border-emerald-700 bg-green-50 dark:bg-emerald-900/30'
                        : 'border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800'
                }`}>
                    <div className="flex items-center justify-center gap-1.5 mb-1">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-green-600" />
                        <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-zinc-400">
                            {game.home_team}
                        </span>
                    </div>
                    <div className={`text-3xl font-black ${homeFavored ? 'text-green-600 dark:text-emerald-400' : 'text-gray-700 dark:text-zinc-200'}`}>
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
