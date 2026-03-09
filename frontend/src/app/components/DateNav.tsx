"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useRef, useState, useEffect } from "react";

const MIN_DATE = "2026-03-07"; // DB has no games before this date
const MAX_DATE = "2026-04-12"; // max selectable date
const MIN = new Date(MIN_DATE);
const MAX = new Date(MAX_DATE);
const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];
const DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function isBeforeMin(year: number, month: number, day: number) {
  const d = new Date(year, month, day);
  return d < MIN;
}

// After April 12, 2026 (April 12 is allowed)
function isAfterMax(year: number, month: number, day: number) {
  if (year > 2026) return true;
  if (year < 2026) return false;
  if (month > 3) return true; // Apr = 3
  if (month < 3) return false;
  return day > 12;
}

function isDateAfterMax(d: Date) {
  const y = d.getFullYear();
  const m = d.getMonth();
  const day = d.getDate();
  if (y > 2026) return true;
  if (y < 2026) return false;
  if (m > 3) return true;
  if (m < 3) return false;
  return day > 12;
}

function toYyyyMmDd(year: number, month: number, day: number) {
  return `${year}${(month + 1).toString().padStart(2, "0")}${day.toString().padStart(2, "0")}`;
}

export default function DateNav({ date: today }: { date: Date }) {
  const router = useRouter();
  const [calendarOpen, setCalendarOpen] = useState(false);
  const [viewYear, setViewYear] = useState(today.getFullYear());
  const [viewMonth, setViewMonth] = useState(today.getMonth());
  const realToday = new Date(); // actual current date for Today button
  const calendarRef = useRef<HTMLDivElement>(null);

  // Click outside to close
  useEffect(() => {
    if (!calendarOpen) return;
    const handle = (e: MouseEvent) => {
      if (
        calendarRef.current &&
        !calendarRef.current.contains(e.target as Node)
      )
        setCalendarOpen(false);
    };
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, [calendarOpen]);

  const d2 = new Date(today);
  d2.setDate(today.getDate() - 2);
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);
  const d4 = new Date(today);
  d4.setDate(today.getDate() + 2);

  const dotw: Record<number, string> = {
    0: "Sun",
    1: "Mon",
    2: "Tue",
    3: "Wed",
    4: "Thu",
    5: "Fri",
    6: "Sat",
  };
  const month: Record<number, string> = {
    0: "Jan",
    1: "Feb",
    2: "Mar",
    3: "Apr",
    4: "May",
    5: "Jun",
    6: "Jul",
    7: "Aug",
    8: "Sep",
    9: "Oct",
    10: "Nov",
    11: "Dec",
  };

  const lastDay = new Date(viewYear, viewMonth + 1, 0).getDate();
  const firstDow = new Date(viewYear, viewMonth, 1).getDay();
  const canGoPrev =
    viewYear > MIN.getFullYear() ||
    (viewYear === MIN.getFullYear() && viewMonth > MIN.getMonth());
  const canGoNext =
    viewYear < MAX.getFullYear() ||
    (viewYear === MAX.getFullYear() && viewMonth < MAX.getMonth());

  const goPrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear((y) => y - 1);
    } else setViewMonth((m) => m - 1);
  };

  const goNextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear((y) => y + 1);
    } else setViewMonth((m) => m + 1);
  };

  const selectDay = (day: number) => {
    if (isBeforeMin(viewYear, viewMonth, day) || isAfterMax(viewYear, viewMonth, day)) return;
    setCalendarOpen(false);
    router.push(`/on/${toYyyyMmDd(viewYear, viewMonth, day)}`);
  };

  const todayHref = `/on/${toYyyyMmDd(realToday.getFullYear(), realToday.getMonth(), realToday.getDate())}`;

  const goToToday = () => {
    setCalendarOpen(false);
    router.push(todayHref);
  };

  const navigateTo = (href: string) => {
    if (typeof document !== "undefined" && "startViewTransition" in document) {
      (
        document as Document & {
          startViewTransition: (cb: () => Promise<void>) => void;
        }
      ).startViewTransition(
        () =>
          new Promise((resolve) => {
            router.push(href);
            setTimeout(resolve, 80);
          }),
      );
    } else {
      router.push(href);
    }
  };

  // One month only: leading empties + days 1..lastDay
  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= lastDay; d++) cells.push(d);

  return (
    <div className="flex items-center justify-center gap-4 mb-12">
      <div className="relative" ref={calendarRef}>
        <button
          type="button"
          onClick={() => {
            setViewYear(today.getFullYear());
            setViewMonth(today.getMonth());
            setCalendarOpen((o) => !o);
          }}
          className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-2 py-1.5 text-zinc-700 shadow-sm hover:bg-zinc-100 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700"
          aria-label="Open calendar"
          aria-expanded={calendarOpen}
        >
          <svg
            className="h-5 w-5"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden
          >
            <rect
              x="3"
              y="4"
              width="18"
              height="17"
              rx="2"
              className="stroke-current"
              strokeWidth="1.5"
            />
            <path d="M3 9h18" className="stroke-current" strokeWidth="1.5" />
            <path d="M9 3v4" className="stroke-current" strokeWidth="1.5" />
            <path d="M15 3v4" className="stroke-current" strokeWidth="1.5" />
          </svg>
        </button>

        {calendarOpen && (
          <div className="absolute left-0 top-full z-50 mt-2 min-w-[280px] rounded-xl border border-zinc-200 bg-white p-4 shadow-lg dark:border-zinc-600 dark:bg-zinc-800">
            <div className="mb-3 flex items-center justify-between gap-2">
              <button
                type="button"
                onClick={goToToday}
                className="rounded-lg bg-blue-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-500"
              >
                Today
              </button>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={goPrevMonth}
                  disabled={!canGoPrev}
                  className="rounded-lg px-2 py-1.5 text-lg hover:bg-zinc-100 disabled:opacity-40 disabled:pointer-events-none dark:hover:bg-zinc-700"
                  aria-label="Previous month"
                >
                  ←
                </button>
                <span className="min-w-[100px] text-center text-base font-semibold text-zinc-800 dark:text-zinc-200">
                  {MONTH_NAMES[viewMonth]} {viewYear}
                </span>
                <button
                  type="button"
                  onClick={goNextMonth}
                  disabled={!canGoNext}
                  className="rounded-lg px-2 py-1.5 text-lg hover:bg-zinc-100 disabled:opacity-40 disabled:pointer-events-none dark:hover:bg-zinc-700"
                  aria-label="Next month"
                >
                  →
                </button>
              </div>
            </div>
            <div className="grid grid-cols-7 gap-1.5 text-center">
              {DOW.map((d) => (
                <div
                  key={d}
                  className="py-1 text-xs font-medium text-zinc-500 dark:text-zinc-400"
                >
                  {d}
                </div>
              ))}
              {cells.map((day, i) => {
                if (day === null) return <div key={`e-${i}`} />;
                const disabled = isBeforeMin(viewYear, viewMonth, day) || isAfterMax(viewYear, viewMonth, day);
                const isToday =
                  realToday.getFullYear() === viewYear &&
                  realToday.getMonth() === viewMonth &&
                  realToday.getDate() === day;
                return (
                  <button
                    key={day}
                    type="button"
                    disabled={disabled}
                    onClick={() => selectDay(day)}
                    className={`aspect-square min-w-[32px] rounded-lg py-1.5 text-sm ${
                      disabled
                        ? "cursor-not-allowed text-zinc-300 dark:text-zinc-600"
                        : "hover:bg-blue-100 dark:hover:bg-blue-900/40"
                    } ${isToday ? "bg-blue-500 text-white hover:bg-blue-600 dark:bg-blue-600 dark:hover:bg-blue-500" : ""}`}
                  >
                    {day}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={() =>
          navigateTo(
            `/on/${yesterday.getFullYear()}${(yesterday.getMonth() + 1).toString().padStart(2, "0")}${yesterday.getDate().toString().padStart(2, "0")}`,
          )
        }
        className="text-xl px-1.5 hover:opacity-60 transition-opacity duration-150"
        aria-label="Previous day"
      >
        ←
      </button>

      <div className="flex gap-10">
        {isDateAfterMax(d2) ? (
          <span className="flex flex-col items-center text-zinc-400 dark:text-zinc-500">
            <span className="font-semibold">{dotw[d2.getDay()]}</span>
            <span>
              {month[d2.getMonth()]} {d2.getDate()}
            </span>
          </span>
        ) : (
          <Link
            href={`/on/${d2.getFullYear()}${(d2.getMonth() + 1).toString().padStart(2, "0")}${d2.getDate().toString().padStart(2, "0")}`}
            className="flex flex-col items-center hover:text-blue-500"
          >
            <span className="font-semibold">{dotw[d2.getDay()]}</span>
            <span>
              {month[d2.getMonth()]} {d2.getDate()}
            </span>
          </Link>
        )}

        {isDateAfterMax(yesterday) ? (
          <span className="flex flex-col items-center text-zinc-400 dark:text-zinc-500">
            <span className="font-semibold">{dotw[yesterday.getDay()]}</span>
            <span>
              {month[yesterday.getMonth()]} {yesterday.getDate()}
            </span>
          </span>
        ) : (
          <Link
            href={`/on/${yesterday.getFullYear()}${(yesterday.getMonth() + 1).toString().padStart(2, "0")}${yesterday.getDate().toString().padStart(2, "0")}`}
            className="flex flex-col items-center hover:text-blue-500"
          >
            <span className="font-semibold">{dotw[yesterday.getDay()]}</span>
            <span>
              {month[yesterday.getMonth()]} {yesterday.getDate()}
            </span>
          </Link>
        )}

        <div className="flex flex-col items-center text-blue-500 font-semibold">
          <span>{dotw[today.getDay()]}</span>
          <span>
            {month[today.getMonth()]} {today.getDate()}
          </span>
        </div>

        {isDateAfterMax(tomorrow) ? (
          <span className="flex flex-col items-center text-zinc-400 dark:text-zinc-500">
            <span className="font-semibold">{dotw[tomorrow.getDay()]}</span>
            <span>
              {month[tomorrow.getMonth()]} {tomorrow.getDate()}
            </span>
          </span>
        ) : (
          <Link
            href={`/on/${tomorrow.getFullYear()}${(tomorrow.getMonth() + 1).toString().padStart(2, "0")}${tomorrow.getDate().toString().padStart(2, "0")}`}
            className="flex flex-col items-center hover:text-blue-500"
          >
            <span className="font-semibold">{dotw[tomorrow.getDay()]}</span>
            <span>
              {month[tomorrow.getMonth()]} {tomorrow.getDate()}
            </span>
          </Link>
        )}

        {isDateAfterMax(d4) ? (
          <span className="flex flex-col items-center text-zinc-400 dark:text-zinc-500">
            <span className="font-semibold">{dotw[d4.getDay()]}</span>
            <span>
              {month[d4.getMonth()]} {d4.getDate()}
            </span>
          </span>
        ) : (
          <Link
            href={`/on/${d4.getFullYear()}${(d4.getMonth() + 1).toString().padStart(2, "0")}${d4.getDate().toString().padStart(2, "0")}`}
            className="flex flex-col items-center hover:text-blue-500"
          >
            <span className="font-semibold">{dotw[d4.getDay()]}</span>
            <span>
              {month[d4.getMonth()]} {d4.getDate()}
            </span>
          </Link>
        )}
      </div>

      <button
        type="button"
        onClick={() =>
          navigateTo(
            `/on/${tomorrow.getFullYear()}${(tomorrow.getMonth() + 1).toString().padStart(2, "0")}${tomorrow.getDate().toString().padStart(2, "0")}`,
          )
        }
        disabled={isDateAfterMax(tomorrow)}
        className="text-xl px-1.5 hover:opacity-60 transition-opacity duration-150 disabled:opacity-40 disabled:pointer-events-none"
        aria-label="Next day"
      >
        →
      </button>
    </div>
  );
}
