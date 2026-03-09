import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { GameDataProvider } from "./GameDataProvider";
import Navbar from "./components/Navbar";
import "./globals.css";

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
        <Navbar />
        <GameDataProvider>{children}</GameDataProvider>
      </body>
    </html>
  );
}