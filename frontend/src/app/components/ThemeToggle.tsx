"use client";

import { useEffect, useState, useSyncExternalStore } from "react";
import Image from "next/image";
import moonSymbol from "../image/moon_symbol.png";
import sunSymbol from "../image/sun_symbol.png";

type Theme = "light" | "dark" | "system";

function getSystemPrefersDark() {
  if (typeof window === "undefined") return false;
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ?? false;
}

function resolveTheme(theme: Theme) {
  if (theme === "system") return getSystemPrefersDark() ? "dark" : "light";
  return theme;
}

function applyTheme(theme: Theme) {
  const resolved = resolveTheme(theme);
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", resolved === "dark");
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === "undefined") return "system";
    try {
      return (localStorage.getItem("theme") as Theme | null) ?? "system";
    } catch {
      return "system";
    }
  });
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  useEffect(() => {
    if (!mounted) return;
    applyTheme(theme);
  }, [mounted, theme]);

  useEffect(() => {
    if (!mounted || typeof window === "undefined") return;
    const mql = window.matchMedia?.("(prefers-color-scheme: dark)");
    const onChange = () => {
      if (theme === "system") {
        applyTheme("system");
      }
    };

    mql?.addEventListener?.("change", onChange);
    return () => mql?.removeEventListener?.("change", onChange);
  }, [mounted, theme]);

  function toggle() {
    const resolved = resolveTheme(theme);
    const next: Theme = resolved === "dark" ? "light" : "dark";
    setTheme(next);
    try {
      localStorage.setItem("theme", next);
    } catch {
      // ignore
    }
  }

  const resolved = resolveTheme(theme);
  const pressed = resolved === "dark";
  const isDark = resolved === "dark";

  if (!mounted) {
    return (
      <button
        type="button"
        aria-label="Toggle dark mode"
        aria-pressed={false}
        className="group relative cursor-pointer p-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40 flex items-center justify-center"
      >
        <span className="pointer-events-none absolute top-full right-0 z-50 mt-2 whitespace-nowrap rounded bg-zinc-800 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100 dark:bg-zinc-100 dark:text-zinc-900">
          Toggle theme
        </span>
        <span className="sr-only">Toggle dark mode</span>
        <Image
          src={sunSymbol}
          alt="Toggle dark mode"
          width={24}
          height={24}
          className="h-6 w-6 transition-opacity group-hover:opacity-80"
        />
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle dark mode"
      aria-pressed={pressed}
      className="group relative cursor-pointer p-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40 flex items-center justify-center"
    >
      <span className="pointer-events-none absolute top-full right-0 z-50 mt-2 whitespace-nowrap rounded bg-zinc-800 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100 dark:bg-zinc-100 dark:text-zinc-900">
        {isDark ? "Switch to light mode" : "Switch to dark mode"}
      </span>
      <span className="sr-only">Toggle dark mode</span>
      <Image
        src={isDark ? moonSymbol : sunSymbol}
        alt={isDark ? "Switch to light mode" : "Switch to dark mode"}
        width={24}
        height={24}
        className="h-6 w-6 transition-opacity group-hover:opacity-80"
      />
    </button>
  );
}
