import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { GameDataProvider } from "./GameDataProvider";
import ThemeToggle from "./components/ThemeToggle";
import "./globals.css";
import Image from "next/image";
import { Playfair_Display } from "next/font/google";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["600"],
});

export const metadata: Metadata = {
  title: "Sports Betting - NBA Win Probabilities & Prop Bets",
  description: "View live win probabilities and prop bets for NBA games",
};

const themeScript = `
(() => {
  try {
    const theme = localStorage.getItem("theme") || "system";
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = theme === "dark" || (theme === "system" && prefersDark);
    document.documentElement.classList.toggle("dark", isDark);
  } catch {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased flex flex-col min-h-screen`}
      >
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
            className="h-14 w-auto"
          />
          <h1 className={`${playfair.className} text-2xl
          bg-gradient-to-r from-blue-900 via-blue-700 to-cyan-700
          dark:from-cyan-400 dark:to-blue-500
          bg-clip-text text-transparent`}>
            Sports Betting
          </h1>
        </div>

        <div className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 flex gap-5">
          <Link
            href="/"
            className="px-5 py-1.5 rounded-full
            bg-gradient-to-r from-cyan-700/70 to-blue-700/70
            hover:from-cyan-500 hover:to-blue-500
            text-white dark:text-slate-200 font-semibold
            transition-all duration-300"
          >
            Games
          </Link>

          <Link
            href="/props"
            className="px-5 py-1.5 rounded-full
            bg-gradient-to-r from-cyan-700/70 to-blue-700/70
            hover:from-cyan-500 hover:to-blue-500
            text-white dark:text-slate-200 font-semibold
            transition-all duration-300"
          >
            Props
          </Link>
        </div>

        <div className="flex items-center justify-end">
          <ThemeToggle />
        </div>

      </nav>
        <GameDataProvider>{children}</GameDataProvider>
      </body>
    </html>
  );
}
