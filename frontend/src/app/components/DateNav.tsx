import Link from "next/link";

export default function DateNav({ date: today }: { date: Date }) {
    
    let d2 = new Date(today);
    d2.setDate(today.getDate() - 2);
    
    let yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    
    let tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);
    
    let d4 = new Date(today);
    d4.setDate(today.getDate() + 2);
    
    let dotw: Record<number, string> = {
        0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed",
        4: "Thu", 5: "Fri", 6: "Sat"
    };
    
    let month: Record<number, string> = {
        0: "Jan", 1: "Feb", 2: "Mar", 3: "Apr",
        4: "May", 5: "Jun", 6: "Jul", 7: "Aug",
        8: "Sep", 9: "Oct", 10: "Nov", 11: "Dec"
    };
    
    return (
        <div className="flex items-center justify-center gap-6 mb-12">
        
            <Link
                href={`/on/${yesterday.getFullYear()}${(yesterday.getMonth()+1).toString().padStart(2,'0')}${yesterday.getDate().toString().padStart(2,'0')}`}
                className="text-2xl px-3 hover:opacity-60"
            >←</Link>
            
            <div className="flex gap-10">
            
            <Link
                href={`/on/${d2.getFullYear()}${(d2.getMonth()+1).toString().padStart(2,'0')}${d2.getDate().toString().padStart(2,'0')}`}
                className="flex flex-col items-center hover:text-blue-500"
            >
                <span className="font-semibold">{dotw[d2.getDay()]}</span>
                <span>{month[d2.getMonth()]} {d2.getDate()}</span>
            </Link>
            
            {/* yesterday */}
            <Link
                href={`/on/${yesterday.getFullYear()}${(yesterday.getMonth()+1).toString().padStart(2,'0')}${yesterday.getDate().toString().padStart(2,'0')}`}
                className="flex flex-col items-center hover:text-blue-500"
            >
                <span className="font-semibold">{dotw[yesterday.getDay()]}</span>
                <span>{month[yesterday.getMonth()]} {yesterday.getDate()}</span>
            </Link>
            
            <div className="flex flex-col items-center text-blue-500 font-semibold">
                <span>{dotw[today.getDay()]}</span>
                <span>{month[today.getMonth()]} {today.getDate()}</span>
            </div>
            
            <Link
                href={`/on/${tomorrow.getFullYear()}${(tomorrow.getMonth()+1).toString().padStart(2,'0')}${tomorrow.getDate().toString().padStart(2,'0')}`}
                className="flex flex-col items-center hover:text-blue-500"
            >
                <span className="font-semibold">{dotw[tomorrow.getDay()]}</span>
                <span>{month[tomorrow.getMonth()]} {tomorrow.getDate()}</span>
            </Link>
            
            <Link
                href={`/on/${d4.getFullYear()}${(d4.getMonth()+1).toString().padStart(2,'0')}${d4.getDate().toString().padStart(2,'0')}`}
                className="flex flex-col items-center hover:text-blue-500"
            >
                <span className="font-semibold">{dotw[d4.getDay()]}</span>
                <span>{month[d4.getMonth()]} {d4.getDate()}</span>
            </Link>
            
            </div>
            
            <Link
                href={`/on/${tomorrow.getFullYear()}${(tomorrow.getMonth()+1).toString().padStart(2,'0')}${tomorrow.getDate().toString().padStart(2,'0')}`}
                className="text-2xl px-3 hover:opacity-60"
            >→</Link>
        
        </div>
    );
}