"use client";

import Link from "next/link";
import Image from "next/image";
import ThemeToggle from "./ThemeToggle";
import { Playfair_Display } from "next/font/google";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, CircleHelp } from "lucide-react";

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["600"],
});

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-6
    bg-slate-200/70 hover:bg-slate-300 dark:bg-[#1b2433]/70 dark:hover:bg-[#1b2433]
    backdrop-blur-md text-white
    border-b border-slate-800
    transition-all duration-300">

    <div className="flex items-center gap-3"> 
        <Link href="/">
          <Image
            src="/logo_light.png"
            alt="Sports Betting"
            width={400}
            height={112}
            className="h-14 w-auto object-contain translate-y-[4px] dark:hidden"
          />
          <Image
            src="/logo_dark.png"
            alt="Sports Betting"
            width={400}
            height={112}
            className="hidden h-14 w-auto object-contain translate-y-[4px] dark:block"
          />
        </Link>
    </div>

    <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 flex gap-10">
    <Link
    href="/"
    className={`relative flex items-center gap-2 font-semibold transition-all duration-200
    ${pathname === "/" || pathname.startsWith("/on/") || pathname.startsWith("/games/")
        ? "text-blue-600 dark:text-blue-400"
        : "text-black dark:text-white hover:text-blue-700 dark:hover:text-blue-400"
    }`}
    >
    <Activity size={18} className="translate-y-[1px]" />
    Games

    {(pathname === "/" || pathname.startsWith("/on/") || pathname.startsWith("/games/")) && (
        <span className="absolute -bottom-2 left-0 right-0 -mx-6 h-[3px] bg-blue-800 rounded-full"></span>
    )}
    </Link>

    <Link
    href="/props"
    className={`relative flex items-center gap-2 font-semibold transition-all duration-200
    ${pathname === "/props"
        ? "text-blue-600 dark:text-blue-400"
        : "text-black dark:text-white hover:text-blue-700 dark:hover:text-blue-400"
    }`}
    >
    <BarChart3 size={18} className="translate-y-[1px]" />
    Props

    {pathname === "/props" && (
        <span className="absolute -bottom-2 left-0 right-0 -mx-6 h-[3px] bg-blue-800 rounded-full"></span>
    )}
    </Link>
    </div>

    <div className="flex items-center justify-end gap-2">
        <ThemeToggle />
        <Link
          href="/info"
          aria-label="How to use this app"
          className={`group relative cursor-pointer p-1 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-white/40 ${
            pathname === "/info"
              ? "text-blue-600 dark:text-blue-400"
              : "text-black dark:text-white hover:text-blue-700 dark:hover:text-blue-400"
          }`}
        >
          <span className="pointer-events-none absolute top-full right-0 z-50 mt-2 whitespace-nowrap rounded bg-zinc-800 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100 dark:bg-zinc-100 dark:text-zinc-900">
            How to use this app
          </span>
          <CircleHelp size={20} />
        </Link>
    </div>

    </nav>
  );
}

