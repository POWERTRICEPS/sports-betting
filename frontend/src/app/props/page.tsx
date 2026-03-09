import { Suspense } from "react";
import PropsPageClient from "./PropsPageClient";
import { useState, useMemo } from "react";
import { mockProps } from "./mock";

export default function PropsPage() {
  const [selectedTeam, setSelectedTeam] = useState<string>("All");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  const uniqueTeams = useMemo(() => {
    const teams = mockProps.map((p) => p.team);
    return Array.from(new Set(teams)).sort();
  }, []);
``
  const filteredProps = useMemo(() => {
    let result = [...mockProps];

    if (selectedTeam !== "All") {
      result = result.filter((p) => p.team === selectedTeam);
    }

    if (selectedCategory !== "All") {
      result.sort((a, b) => {
        const key = selectedCategory.toLowerCase() as "pts" | "reb" | "ast";
        return b.projected[key] - a.projected[key];
      });
    }

    return result;
  }, [selectedTeam, selectedCategory]);

  const clearFilters = () => {
    setSelectedTeam("All");
    setSelectedCategory("All");
  };

  return (
    <Suspense fallback={<main className="min-h-screen bg-zinc-50 dark:bg-zinc-950 p-6 pt-20" />}>
      <PropsPageClient />
    </Suspense>
  );
}
