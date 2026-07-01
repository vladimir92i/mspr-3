"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Train, Moon, Sun, Leaf, Clock, Ruler, Building2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TripDetail } from "@/app/types/routes";
import { formatDuration, co2Avion } from "@/app/lib/utils";
import StopsTimeline from "@/app/components/StopsTimeline";

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function TrajetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<TripDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const apiUrl = process.env.API_URL ?? "http://localhost:8000";
    fetch(`${apiUrl}/api/trajets/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Trajet introuvable (HTTP ${res.status})`);
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32 text-slate-400" role="status" aria-live="polite">
        <svg
          className="animate-spin w-5 h-5 mr-2"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
        Chargement du trajet…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 flex flex-col gap-4">
        <div className="rounded-lg bg-red-50 border border-red-200 px-5 py-4 text-sm text-red-700" role="alert">
          <strong>Erreur :</strong> {error ?? "Trajet introuvable."}
        </div>
        <Link
          href="/"
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 transition-colors w-fit"
        >
          <ArrowLeft className="w-4 h-4" /> Retour aux trajets
        </Link>
      </div>
    );
  }

  const { trip, agency, is_night_train, stops } = data;
  const emissionTrain = parseFloat(trip.emission);
  const emissionAvion = co2Avion(trip.distance);
  const saving = Math.round(((emissionAvion - emissionTrain) / emissionAvion) * 100);

  // Détecter si le train arrive le lendemain
  const depH = trip?.departure_time ? parseInt(trip.departure_time.split(":")[0]) : 0;
  const arrH = trip?.arrival_time ? parseInt(trip.arrival_time.split(":")[0]) : 0;
  const nextDay = arrH < depH;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6">
      {/* Retour */}
      <Link
        href="/"
        className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 transition-colors w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        Retour aux trajets
      </Link>

      {/* En-tête */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-semibold text-slate-900">{trip.name}</h1>
            {is_night_train ? (
              <Badge className="bg-indigo-950 text-indigo-300 rounded-full gap-1">
                <Moon className="w-3 h-3" aria-hidden="true" /> Nuit
              </Badge>
            ) : (
              <Badge className="bg-amber-100 text-amber-700 rounded-full gap-1">
                <Sun className="w-3 h-3" aria-hidden="true" /> Jour
              </Badge>
            )}
          </div>
          <p className="text-sm text-slate-500 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5" aria-hidden="true" />
            {agency.name}
            <span className="text-slate-300">·</span>
            <span className="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{agency.code}</span>
          </p>
        </div>
      </div>

      {/* Itinéraire principal */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
        <p className="text-xs text-slate-400 uppercase tracking-wide font-medium mb-5">Itinéraire</p>
        <div className="flex items-center justify-between gap-4">
          {/* Départ */}
          <div className="flex flex-col gap-0.5">
            <p className="text-2xl font-semibold text-slate-900">{trip.origin}</p>
            <p className="text-lg font-mono text-slate-600">{trip.departure_time?.slice(0, 5) ?? "—"}</p>
          </div>

          {/* Ligne du milieu */}
          <div className="flex-1 flex flex-col items-center px-4 gap-1">
            <span className="text-xs text-slate-400">{formatDuration(trip.duration)}</span>
            <div className="w-full flex items-center gap-2">
              <div className="w-2 h-2 rounded-full border-2 border-slate-400 shrink-0" aria-hidden="true" />
              <div className="flex-1 h-px bg-slate-200" />
              <Train className="w-5 h-5 text-slate-400" aria-hidden="true" />
              <div className="flex-1 h-px bg-slate-200" />
              <div className="w-2 h-2 rounded-full bg-slate-800 shrink-0" aria-hidden="true" />
            </div>
            <span className="text-xs text-slate-400">{stops.length} arrêts</span>
          </div>

          {/* Arrivée */}
          <div className="flex flex-col gap-0.5 text-right">
            <p className="text-2xl font-semibold text-slate-900">{trip.destination}</p>
            <p className="text-lg font-mono text-slate-600">
              {trip.arrival_time?.slice(0, 5) ?? "—"}
              {nextDay && <span className="text-xs text-slate-400 ml-1">+1</span>}
            </p>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          {
            icon: <Ruler className="w-4 h-4 text-slate-400" />,
            label: "Distance",
            value: `${trip.distance.toLocaleString()} km`,
          },
          { icon: <Clock className="w-4 h-4 text-slate-400" />, label: "Durée", value: formatDuration(trip.duration) },
          { icon: <Building2 className="w-4 h-4 text-slate-400" />, label: "Opérateur", value: agency.code },
          { icon: <Leaf className="w-4 h-4 text-green-500" />, label: "CO₂ train", value: `${emissionTrain} kg` },
        ].map(({ icon, label, value }) => (
          <div key={label} className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col gap-2">
            <div className="flex items-center gap-1.5">
              {icon}
              <span className="text-xs text-slate-400 uppercase tracking-wide">{label}</span>
            </div>
            <span className="text-xl font-semibold text-slate-900">{value}</span>
          </div>
        ))}
      </div>

      {/* Empreinte carbone */}
      <div className="bg-green-50 border border-green-200 rounded-xl p-5 flex items-center gap-4">
        <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center shrink-0">
          <Leaf className="w-5 h-5 text-green-600" aria-hidden="true" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-green-900">Impact environnemental</p>
          <p className="text-xs text-green-700 mt-0.5">
            Ce trajet en train émet <strong>{emissionTrain} kg CO₂</strong> par passager, contre environ{" "}
            <strong>{emissionAvion} kg</strong> en avion sur la même distance.
          </p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-2xl font-bold text-green-600">−{saving}%</p>
          <p className="text-xs text-green-600">d`&apos;`émissions</p>
        </div>
      </div>

      {/* Arrêts */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <p className="text-xs text-slate-400 uppercase tracking-wide font-medium">Arrêts</p>
          <span className="text-xs text-slate-400">{stops.length} gares</span>
        </div>
        <StopsTimeline stops={stops} />
      </div>
    </div>
  );
}
