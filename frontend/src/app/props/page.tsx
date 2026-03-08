import { Suspense } from "react";
import PropsPageClient from "./PropsPageClient";

export default function PropsPage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-zinc-50 dark:bg-zinc-950 p-6 pt-20" />}>
      <PropsPageClient />
    </Suspense>
  );
}
