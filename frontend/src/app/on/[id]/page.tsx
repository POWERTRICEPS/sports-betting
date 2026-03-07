import GamesByDate from "./gamesByDate";
import { redirect } from "next/navigation";

function dateToId(date: Date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2,"0"),
    String(date.getDate()).padStart(2,"0"),
  ].join("");
}

export default async function GamesPage({ params }: { params: { id: string } }) {
    const p = await params;
    const todayId = dateToId(new Date());

    if (p.id === todayId) {
        redirect(`/`);
    }

    return(<GamesByDate id={p.id} />);
}
/* <div className="">
        <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-white">
          GC1.
        </h1>
      </div>
      <div className="a2 rounded-lg border border-zinc-200 dark:border-zinc-800 p-4">
        <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-white">
          GC2
        </h1>
      </div>
*/