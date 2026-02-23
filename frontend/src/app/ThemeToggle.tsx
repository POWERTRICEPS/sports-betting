"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark" | "system";

function getSystemPrefersDark() {
  return window.matchMedia?.("(prefers-color-scheme: dark)")?.matches ?? false;
}

function resolveTheme(theme: Theme) {
  if (theme === "system") return getSystemPrefersDark() ? "dark" : "light";
  return theme;
}

function applyTheme(theme: Theme) {
  const resolved = resolveTheme(theme);
  document.documentElement.classList.toggle("dark", resolved === "dark");
}

export default function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const [theme, setTheme] = useState<Theme>("system");

  useEffect(() => {
    setMounted(true);
    try {
      const stored = (localStorage.getItem("theme") as Theme | null) ?? "system";
      setTheme(stored);
      applyTheme(stored);
    } catch {
      applyTheme("system");
    }

    const mql = window.matchMedia?.("(prefers-color-scheme: dark)");
    const onChange = () => {
      try {
        const stored = (localStorage.getItem("theme") as Theme | null) ?? "system";
        if (stored === "system") applyTheme("system");
      } catch {
        applyTheme("system");
      }
    };

    mql?.addEventListener?.("change", onChange);
    return () => mql?.removeEventListener?.("change", onChange);
  }, []);

  function toggle() {
    const next: Theme = resolveTheme(theme) === "dark" ? "light" : "dark";
    setTheme(next);
    try {
      localStorage.setItem("theme", next);
    } catch {
      // ignore
    }
    applyTheme(next);
  }

  const resolved = mounted ? resolveTheme(theme) : "light";
  // Label reflects the *next* theme when clicked
  const label = mounted
    ? resolved === "dark"
      ? "Light"
      : "Dark"
    : "Theme";
  const pressed = mounted && resolved === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label="Toggle dark mode"
      aria-pressed={pressed}
      className="rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-sm font-semibold text-white hover:bg-white/15 focus:outline-none focus:ring-2 focus:ring-white/40"
    >
      {label} mode
    </button>
  );
}

