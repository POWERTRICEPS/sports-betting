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

/* ------------------------------------------------------------------ */
/*  Public types                                                       */
/* ------------------------------------------------------------------ */

/** A single ML-probability snapshot captured from the backend. */
export interface ProbSnapshot {
    home: number;          // home_win_prob from backend ML model
    away: number;          // away_win_prob from backend ML model
    homeScore: number | null;
    awayScore: number | null;
    label: string;         // game status at time of capture (e.g. "Q1 8:30")
}

/* ------------------------------------------------------------------ */
/*  Internal types                                                     */
/* ------------------------------------------------------------------ */

interface DataPoint {
    label: string;
    home: number;
    away: number;
    /** Where this data point came from */
    source: 'model' | 'final';
    /** Home probability change from previous point */
    homeDelta: number | null;
    /** Cumulative score difference (home − away) */
    scoreDiff: number | null;
    /** Home score at this snapshot */
    homeScore: number | null;
    /** Away score at this snapshot */
    awayScore: number | null;
}

interface WinProbabilityGraphProps {
    game: Game;
    probHistory: ProbSnapshot[];
}

/* ------------------------------------------------------------------ */
/*  Build data-point array from accumulated snapshots                  */
/* ------------------------------------------------------------------ */

function buildDataPoints(
    snapshots: ProbSnapshot[],
    isFinal: boolean,
): DataPoint[] {
    return snapshots.map((snap, i) => {
        const prevHome = i > 0 ? snapshots[i - 1].home : null;
        const isLast = i === snapshots.length - 1;

        return {
            label: snap.label,
            home: snap.home,
            away: snap.away,
            source: isLast && isFinal ? 'final' : 'model',
            homeDelta: prevHome != null ? +(snap.home - prevHome).toFixed(1) : null,
            scoreDiff:
                snap.homeScore != null && snap.awayScore != null
                    ? snap.homeScore - snap.awayScore
                    : null,
            homeScore: snap.homeScore,
            awayScore: snap.awayScore,
        };
    });
}

/* ------------------------------------------------------------------ */
/*  Source labels                                                       */
/* ------------------------------------------------------------------ */

const SOURCE_LABELS: Record<DataPoint['source'], { text: string; color: string }> = {
    model: { text: 'ML Model', color: 'text-emerald-600 dark:text-emerald-400' },
    final: { text: 'Final Result', color: 'text-gray-600 dark:text-zinc-300' },
};

/* ------------------------------------------------------------------ */
/*  Custom tooltip                                                     */
/* ------------------------------------------------------------------ */

function ProbTooltip({ active, payload, label }: any) {
    if (!active || !payload?.length) return null;
    const home = payload.find((p: any) => p.dataKey === 'home');
    const away = payload.find((p: any) => p.dataKey === 'away');
    const dataPoint: DataPoint | undefined = payload[0]?.payload;
    const sourceInfo = dataPoint ? SOURCE_LABELS[dataPoint.source] : null;
    const delta = dataPoint?.homeDelta;

    return (
        <div className="rounded-lg border border-gray-200 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2.5 shadow-lg text-xs min-w-[180px]">
            {/* Header */}
            <div className="flex items-center justify-between gap-3 mb-1.5">
                <span className="font-semibold text-gray-700 dark:text-zinc-200">{label}</span>
                {sourceInfo && (
                    <span className={`text-[10px] font-medium ${sourceInfo.color}`}>
                        {sourceInfo.text}
                    </span>
                )}
            </div>

            {/* Probabilities */}
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

            {/* Divider */}
            {(delta != null || dataPoint?.scoreDiff != null) && (
                <hr className="my-1.5 border-gray-200 dark:border-zinc-600" />
            )}

            {/* Delta */}
            {delta != null && (
                <div className="flex items-center gap-1.5">
                    <span className="text-gray-500 dark:text-zinc-400">Δ Home:</span>
                    <span className={`font-semibold ${delta > 0 ? 'text-green-600 dark:text-green-400' : delta < 0 ? 'text-red-500 dark:text-red-400' : 'text-gray-500 dark:text-zinc-400'}`}>
                        {delta > 0 ? '+' : ''}{delta}%
                    </span>
                </div>
            )}

            {/* Score info */}
            {dataPoint?.homeScore != null && dataPoint?.awayScore != null && (
                <div className="flex items-center gap-1.5">
                    <span className="text-gray-500 dark:text-zinc-400">Score:</span>
                    <span className="font-semibold text-gray-800 dark:text-zinc-200">
                        {dataPoint.homeScore} – {dataPoint.awayScore}
                    </span>
                    <span className={`text-[10px] font-medium ${
                        (dataPoint.scoreDiff ?? 0) > 0 ? 'text-green-600 dark:text-green-400' :
                        (dataPoint.scoreDiff ?? 0) < 0 ? 'text-red-500 dark:text-red-400' :
                        'text-gray-500 dark:text-zinc-400'
                    }`}>
                        ({(dataPoint.scoreDiff ?? 0) > 0 ? '+' : ''}{dataPoint.scoreDiff})
                    </span>
                </div>
            )}
        </div>
    );
}

/* ------------------------------------------------------------------ */
/*  Custom dot                                                         */
/* ------------------------------------------------------------------ */

function CustomDot({ cx, cy, payload, baseColor }: any) {
    if (cx == null || cy == null) return null;
    const dp: DataPoint = payload;

    if (dp.source === 'final') {
        // Square for final result
        const s = 4;
        return (
            <rect
                x={cx - s}
                y={cy - s}
                width={s * 2}
                height={s * 2}
                fill={baseColor}
                stroke="#fff"
                strokeWidth={1.5}
            />
        );
    }

    // Standard filled circle for ML model points
    return <circle cx={cx} cy={cy} r={4} fill={baseColor} strokeWidth={0} />;
}

/* ------------------------------------------------------------------ */
/*  Main component                                                     */
/* ------------------------------------------------------------------ */

export default function WinProbabilityGraph({ game, probHistory }: WinProbabilityGraphProps) {
    if (!game) return null;

    const isFinal = game.status === 'Final';
    const data = buildDataPoints(probHistory, isFinal);

    const homeProb = game.home_win_prob ?? 50;
    const awayProb = game.away_win_prob ?? 50;
    const homeFavored = homeProb >= awayProb;

    // Calculate a sensible X-axis tick interval so labels don't overlap
    const tickInterval = data.length <= 8 ? 0 : Math.floor(data.length / 7);

    return (
        <div className="mt-10 mx-auto max-w-4xl">
            <h4 className="text-center text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-1">
                Win Probability
            </h4>
            <p className="text-center text-xs text-gray-500 dark:text-zinc-400 mb-4">
                {game.away_team} vs {game.home_team}
            </p>

            {/* Empty-state message when no ML data is available yet */}
            {data.length === 0 && (
                <div className="text-center mb-4">
                    <span className="inline-flex items-center gap-1 rounded-full bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 px-3 py-1 text-xs font-medium text-gray-500 dark:text-zinc-400">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
                        </svg>
                        Waiting for ML probability data from the backend…
                    </span>
                </div>
            )}

            {/* Chart */}
            {data.length > 0 && (
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
                                tick={{ fontSize: 11, fill: '#6b7280' }}
                                axisLine={{ stroke: '#d1d5db' }}
                                tickLine={false}
                                interval={tickInterval}
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
                                dot={(props: any) => <CustomDot {...props} baseColor="#16a34a" />}
                                activeDot={{ r: 6, fill: '#16a34a', stroke: '#fff', strokeWidth: 2 }}
                            />
                            <Area
                                type="monotone"
                                dataKey="away"
                                name="Away"
                                stroke="#ef4444"
                                strokeWidth={2.5}
                                fill="url(#gradAway)"
                                dot={(props: any) => <CustomDot {...props} baseColor="#ef4444" />}
                                activeDot={{ r: 6, fill: '#ef4444', stroke: '#fff', strokeWidth: 2 }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Data source legend */}
            {data.length > 0 && (
                <div className="flex items-center justify-center gap-5 mt-4 mb-2 flex-wrap">
                    {data.some(d => d.source === 'model') && (
                        <div className="flex items-center gap-1.5 text-[11px] text-gray-500 dark:text-zinc-400">
                            <span className="inline-block h-2.5 w-2.5 rounded-full bg-gray-500" />
                            <span>ML Model</span>
                        </div>
                    )}
                    {data.some(d => d.source === 'final') && (
                        <div className="flex items-center gap-1.5 text-[11px] text-gray-500 dark:text-zinc-400">
                            <span className="inline-block h-2.5 w-2.5 bg-gray-500" />
                            <span>Final Result</span>
                        </div>
                    )}
                </div>
            )}

            {/* Current probability cards */}
            <div className="grid grid-cols-2 gap-4 mt-4">
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
