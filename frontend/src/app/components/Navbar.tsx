"use client";

import Link from "next/link";
import Image from "next/image";
import ThemeToggle from "./ThemeToggle";
import { Playfair_Display } from "next/font/google";
import { usePathname } from "next/navigation";

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

      <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 flex gap-5">
        <Link
          href="/"
          className={`px-5 py-1.5 rounded-full
          bg-gradient-to-r from-cyan-700/60 to-blue-700/50
          hover:from-cyan-500 hover:to-blue-500
          text-white dark:text-slate-200 font-semibold
          transition-all duration-300
          ${pathname === "/" ? "scale-[0.85] shadow-[0_0_12px_3px_rgba(0,0,0,0.25)] dark:shadow-[0_0_12px_3px_rgba(255,255,255,0.25)]" : ""}
          `}
        >
          Games
        </Link>

        <Link
          href="/props"
          className={`px-5 py-1.5 rounded-full
          bg-gradient-to-r from-cyan-700/60 to-blue-700/60
          hover:from-cyan-500 hover:to-blue-500
          text-white dark:text-slate-200 font-semibold
          transition-all duration-300
          ${pathname === "/props" ? "scale-[0.85] shadow-[0_0_12px_3px_rgba(0,0,0,0.25)] dark:shadow-[0_0_12px_3px_rgba(255,255,255,0.25)]" : ""}
          `}
        >
          Props
        </Link>
      </div>

      <div className="flex items-center justify-end">
        <ThemeToggle />
      </div>

    </nav>
  );
}