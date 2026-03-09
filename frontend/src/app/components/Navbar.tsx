"use client";

import Link from "next/link";
import Image from "next/image";
import ThemeToggle from "./ThemeToggle";
import { Playfair_Display } from "next/font/google";
import { usePathname } from "next/navigation";
import { Activity, BarChart3 } from "lucide-react";

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["600"],
});

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="group absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-6
    bg-slate-200/70 hover:bg-slate-300 dark:bg-[#1b2433]/70 dark:hover:bg-[#1b2433]
    backdrop-blur-md text-white
    border-b border-slate-800
    transition-all duration-300">

    <div className="flex items-center gap-3">
        <Image
          src="/logo2.png"
          alt="Sports Betting"
          width={200}
          height={200}
          className="h-14 w-auto object-contain translate-y-[4px]"
        />
        <Link href="/">
          <h1 className={`${playfair.className} text-2xl text-slate-900 dark:text-white cursor-pointer hover:opacity-80 transition`}>
            Sports Betting
          </h1>
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

    <div className="flex items-center justify-end">
        <ThemeToggle />
    </div>

    </nav>
  );
}