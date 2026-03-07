"use client";

import { useEffect, useState } from "react";
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

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mql = window.matchMedia?.("(prefers-color-scheme: dark)");
    const onChange = () => {
      if (theme === "system") {
        applyTheme("system");
      }
    };

    mql?.addEventListener?.("change", onChange);
    return () => mql?.removeEventListener?.("change", onChange);
  }, [theme]);

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

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle dark mode"
      aria-pressed={pressed}
      className="rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-sm font-semibold text-white hover:bg-white/15 focus:outline-none focus:ring-2 focus:ring-white/40 flex items-center justify-center"
    >
      <span className="sr-only">Toggle dark mode</span>
      <Image
        src={isDark ? moonSymbol : sunSymbol}
        alt={isDark ? "Switch to light mode" : "Switch to dark mode"}
        width={24}
        height={24}
        className="h-6 w-6"
      />
    </button>
  );
}

