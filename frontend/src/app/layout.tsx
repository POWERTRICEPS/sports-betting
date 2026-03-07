import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { GameDataProvider } from "./GameDataProvider";
import ThemeToggle from "./components/ThemeToggle";
import "./globals.css";
import Image from "next/image";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
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
      <nav className="absolute top-0 left-0 right-0 h-16 flex items-center justify-between px-6 bg-blue-900/75 backdrop-blur-md text-white">
        <div className="flex items-center gap-3">
          <Image
          src="/logo2.png"
          alt="Sports Betting"
          width={200}
          height={200}
          className="h-14 w-auto"
        />
          <h1 className="text-xl font-bold tracking-tight">
            PJ09 Sports Betting
          </h1>
        </div>
        <div className="abcd absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 flex gap-2">
          <Link href="/" className="hover:bg-blue-800 text-white font-semibold py-2 px-4 rounded-lg">
            Games
          </Link>
          <Link href="/props" className="hover:bg-blue-800 text-white font-semibold py-2 px-4 rounded-lg">
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
