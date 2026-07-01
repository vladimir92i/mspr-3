import { Stop } from "@/app/types/routes";

export default function StopsTimeline({ stops }: { stops: Stop[] }) {
  return (
    <ol className="relative flex flex-col gap-0" aria-label="Liste des arrêts">
      {stops.map((stop, i) => {
        const isFirst = i === 0;
        const isLast = i === stops.length - 1;
        const time = stop.departure_time ?? stop.arrival_time;

        return (
          <li key={stop.stop_sequence} className="flex gap-4 items-stretch">
            {/* Timeline visuelle */}
            <div className="flex flex-col items-center w-5 shrink-0">
              <div className={`w-px flex-1 ${isFirst ? "bg-transparent" : "bg-slate-200"}`} />
              <div
                className={`w-3 h-3 rounded-full border-2 shrink-0 ${
                  isFirst || isLast ? "border-slate-900 bg-slate-900" : "border-slate-400 bg-white"
                }`}
                aria-hidden="true"
              />
              <div className={`w-px flex-1 ${isLast ? "bg-transparent" : "bg-slate-200"}`} />
            </div>

            {/* Contenu */}
            <div
              className={`flex items-center justify-between gap-4 py-3 flex-1 ${
                !isLast ? "border-b border-slate-100" : ""
              }`}
            >
              <div className="flex flex-col gap-0.5">
                <span className={`text-sm ${isFirst || isLast ? "font-semibold text-slate-900" : "text-slate-700"}`}>
                  {stop.station_name}
                </span>
                {stop.city && <span className="text-xs text-slate-400">{stop.city}</span>}
              </div>
              <span
                className={`text-sm font-mono tabular-nums shrink-0 ${
                  isFirst || isLast ? "font-semibold text-slate-900" : "text-slate-500"
                }`}
              >
                {time?.slice(0, 5) ?? "—"}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
