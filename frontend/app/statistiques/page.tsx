"use client";

import { useEffect, useState } from "react";
import { ApiStatsResponse, StatsData } from "@/app/types/routes";
 
const API_BASE_URL = process.env.API_URL ?? "http://localhost:8000";

function buildStatsData(payload: ApiStatsResponse): StatsData {
  return {
    total: payload.nb_total_trips,
    jour: payload.nb_day_trips,
    nuit: payload.nb_night_trips,
    nbOperateurs: payload.nb_operators,
    parOperateur: Object.entries(payload.trips_by_operator)
      .map(([operateur, total]) => ({ operateur, total }))
      .sort((a, b) => b.total - a.total),
  };
}

function DonutChart({ jour, nuit }: { jour: number; nuit: number }) {
  const total = jour + nuit;
  const r = 60;
  const cx = 80;
  const cy = 80;
  const circ = 2 * Math.PI * r;
  const jourFrac = jour / total;
  const nuitFrac = nuit / total;
  const jourDash = circ * jourFrac;
  const nuitDash = circ * nuitFrac;
  const startOffset = circ * 0.25;
  const nuitOffset = startOffset;
  const jourOffset = startOffset - nuitDash;

  return (
    <svg
      viewBox="0 0 160 160"
      className="w-40 h-40"
      aria-label={`Répartition : ${jour} trains de jour, ${nuit} trains de nuit`}
      role="img"
    >
      {/* Arc nuit */}
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke="#4338ca"
        strokeWidth="24"
        strokeDasharray={`${nuitDash} ${circ - nuitDash}`}
        strokeDashoffset={nuitOffset}
        strokeLinecap="butt"
      />
      {/* Arc jour */}
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke="#f97316"
        strokeWidth="24"
        strokeDasharray={`${jourDash} ${circ - jourDash}`}
        strokeDashoffset={jourOffset}
        strokeLinecap="butt"
      />
      <text
        x={cx}
        y={cy - 8}
        textAnchor="middle"
        className="text-xl font-bold"
        fontSize="22"
        fill="currentColor"
      >
        {total}
      </text>
      <text x={cx} y={cy + 14} textAnchor="middle" fontSize="11" fill="#6b7280">
        trajets
      </text>
    </svg>
  );
}

// Barre horizontale pour les opérateurs
function BarRow({
  label,
  total,
  max,
}: {
  label: string;
  total: number;
  max: number;
}) {
  const width = (total / max) * 100;
  return (
    <div className="flex items-center gap-3" role="row">
      <span
        className="w-28 text-sm text-slate-600 shrink-0 truncate"
        title={label}
      >
        {label}
      </span>
      <div className="flex-1 flex flex-col gap-1">
        <div
          className="h-2 rounded-full overflow-hidden bg-slate-100"
          aria-label={`${label} : ${total} trajets`}
        >
          <div
            className="h-full bg-slate-900 rounded-full"
            style={{ width: `${width}%` }}
          />
        </div>
      </div>
      <span className="w-8 text-sm text-right text-slate-700 font-medium">
        {total}
      </span>
    </div>
  );
}

export default function StatistiquesPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();

    async function loadStats() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${API_BASE_URL}/api/trajets/stats/volumes`,
          {
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          throw new Error(`Erreur API ${response.status}`);
        }

        const payload: ApiStatsResponse = await response.json();
        setStats(buildStatsData(payload));
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Impossible de charger les statistiques.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadStats();

    return () => controller.abort();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-slate-600">
        Chargement des statistiques...
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
          {error ?? "Impossible de charger les statistiques."}
        </div>
      </div>
    );
  }

  const maxOp = Math.max(...stats.parOperateur.map((o) => o.total), 1);
  const pctJour = Math.round((stats.jour / stats.total) * 100);
  const pctNuit = Math.round((stats.nuit / stats.total) * 100);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8">
      {/* En-tête */}
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          Statistiques ferroviaires
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Indicateurs clés sur les dessertes européennes — données chargées
          depuis l’API.
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          {
            label: "Total trajets",
            value: stats.total,
            color: "text-slate-900",
          },
          {
            label: "Trains de jour",
            value: `${stats.jour} (${pctJour}%)`,
            color: "text-orange-600",
          },
          {
            label: "Trains de nuit",
            value: `${stats.nuit} (${pctNuit}%)`,
            color: "text-indigo-600",
          },
          {
            label: "Opérateurs",
            value: stats.nbOperateurs,
            color: "text-slate-900",
          },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className="bg-white border border-slate-200 rounded-xl p-5 flex flex-col gap-1 shadow-sm"
          >
            <span className="text-xs text-slate-500 uppercase tracking-wide">
              {label}
            </span>
            <span className={`text-2xl font-bold ${color}`}>{value}</span>
          </div>
        ))}
      </div>

      {/* Répartition jour/nuit + volumes opérateurs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Donut */}
        <section
          className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4"
          aria-labelledby="chart-repartition"
        >
          <h2
            id="chart-repartition"
            className="text-sm font-semibold text-slate-700 uppercase tracking-wide"
          >
            Répartition jour / nuit
          </h2>
          <div className="flex items-center justify-center gap-8 pt-15">
            <DonutChart jour={stats.jour} nuit={stats.nuit} />
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full bg-orange-400 shrink-0"
                  aria-hidden="true"
                />
                <span className="text-sm text-slate-600">Jour</span>
                <span className="ml-auto font-semibold text-orange-600">
                  {stats.jour}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full bg-indigo-600 shrink-0"
                  aria-hidden="true"
                />
                <span className="text-sm text-slate-600">Nuit</span>
                <span className="ml-auto font-semibold text-indigo-600">
                  {stats.nuit}
                </span>
              </div>
              <div className="border-t pt-3 flex items-center gap-2">
                <span className="text-sm text-slate-500">Total</span>
                <span className="ml-auto font-bold">{stats.total}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Barres opérateurs */}
        <section
          className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4 "
          aria-labelledby="chart-operateurs"
        >
          <h2
            id="chart-operateurs"
            className="text-sm font-semibold text-slate-700 uppercase tracking-wide"
          >
            Volumes par opérateur
          </h2>
          <div
            className="flex flex-col gap-3"
            role="table"
            aria-label="Trajets par opérateur"
          >
            <div className="flex items-center gap-3 mb-1" role="row">
              <span className="w-28 text-xs text-slate-400">Opérateur</span>
              <div className="flex-1 text-xs text-slate-400">Volume</div>
              <span className="w-8 text-xs text-slate-400 text-right">
                Total
              </span>
            </div>
            <div className="flex flex-col gap-3 overflow-y-auto max-h-64 pr-2">
              {stats.parOperateur.map((op) => (
                <BarRow
                  key={op.operateur}
                  label={op.operateur}
                  total={op.total}
                  max={maxOp}
                />
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
