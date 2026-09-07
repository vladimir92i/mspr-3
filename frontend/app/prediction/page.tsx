"use client";

import { useState, useRef, useId } from "react";

interface PredictionOutput {
  emission_predicted: number;
  emission_unit: string;
  distance: number;
}

interface BackendPredictionResponse {
  distance_km?: number;
  predicted_co2_kg?: number;
  distance?: number;
  emission_predicted?: number;
  emission_unit?: string;
}

type Status = "idle" | "loading" | "success" | "error";

const MIN_DISTANCE = 405;
const MAX_DISTANCE = 1847;

export default function PredictPage() {
  const [distance, setDistance] = useState<string>("");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<PredictionOutput | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");

  const inputId = useId();
  const resultRef = useRef<HTMLDivElement>(null);
  const liveRef = useRef<HTMLDivElement>(null);

  function getValidationError(val: string): string {
    if (val === "") return "Veuillez saisir une distance.";
    const n = Number(val);
    if (!Number.isInteger(n) || isNaN(n)) return "La distance doit être un nombre entier.";
    if (n < MIN_DISTANCE || n > MAX_DISTANCE)
      return `La distance doit être comprise entre ${MIN_DISTANCE} et ${MAX_DISTANCE} km.`;
    return "";
  }

  function normalizePredictionOutput(payload: BackendPredictionResponse): PredictionOutput {
    const predicted = payload.predicted_co2_kg ?? payload.emission_predicted;
    const traveledDistance = payload.distance_km ?? payload.distance;

    if (typeof predicted !== "number" || typeof traveledDistance !== "number") {
      throw new Error("Réponse API invalide: format inattendu.");
    }

    return {
      emission_predicted: predicted,
      emission_unit: payload.emission_unit ?? "kg CO₂",
      distance: traveledDistance,
    };
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const validationError = getValidationError(distance);
    if (validationError) {
      setStatus("error");
      setErrorMsg(validationError);
      return;
    }
    setStatus("loading");
    setResult(null);
    setErrorMsg("");
    if (liveRef.current) liveRef.current.textContent = "Calcul en cours…";
    try {
      const res = await fetch(`/api/predict?distance=${Number(distance)}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail ?? `Erreur serveur (${res.status})`);
      }
      const rawData: BackendPredictionResponse = await res.json();
      const data = normalizePredictionOutput(rawData);
      setResult(data);
      setStatus("success");
      if (liveRef.current) liveRef.current.textContent = `Résultat : ${data.emission_predicted} ${data.emission_unit}`;
      setTimeout(() => resultRef.current?.focus(), 50);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Erreur inconnue.";
      setErrorMsg(message);
      setStatus("error");
      if (liveRef.current) liveRef.current.textContent = `Erreur : ${message}`;
    }
  }

  const validationError = status !== "idle" ? getValidationError(distance) : "";
  const inputInvalid = status === "error" && validationError !== "";
  const errorId = `${inputId}-error`;
  const descId = `${inputId}-desc`;

  return (
    <div className="obrail-root">
      <style>{`
        /* ── Variables (scoped sur le wrapper) ── */
        .obrail-root {
          --rail-blue:     #155DFC;
          --rail-dark:     #0D2B7A;
          --rail-light:    #E8EFFF;
          --rail-green:    #1A9B5F;
          --rail-green-bg: #E6F7F0;
          --rail-red:      #C0392B;
          --rail-red-bg:   #FDECEA;
          --gray-50:       #F8FAFC;
          --gray-100:      #F1F5F9;
          --gray-300:      #CBD5E1;
          --gray-500:      #64748B;
          --gray-700:      #334155;
          --gray-900:      #0F172A;
          --white:         #FFFFFF;
          --radius:        10px;
          --shadow:        0 4px 24px rgba(21,93,252,0.10);
 
          /* styles base (remplace l'ancien "body") */
          font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
          background: var(--gray-50);
          color: var(--gray-900);
          min-height: 100vh;
          line-height: 1.5;
          box-sizing: border-box;
        }
 
        /* ── Reset scoped (ne touche plus au reste de la page) ── */
        .obrail-root *, .obrail-root *::before, .obrail-root *::after {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
 
        /* ── Skip link (RGAA 12.11) ── */
        .obrail-root .skip-link {
          position: absolute;
          left: -999px;
          top: auto;
          width: 1px;
          height: 1px;
          overflow: hidden;
          background: var(--rail-blue);
          color: var(--white);
          padding: 12px 20px;
          border-radius: 0 0 var(--radius) var(--radius);
          font-weight: 600;
          font-size: 0.95rem;
          text-decoration: none;
          z-index: 9999;
        }
        .obrail-root .skip-link:focus {
          position: fixed;
          left: 50%;
          transform: translateX(-50%);
          width: auto;
          height: auto;
        }
 
        /* ── Layout ── */
        .obrail-root .page-header {
          background: var(--white);
          border-bottom: 3px solid var(--rail-blue);
          padding: 0 24px;
        }
        .obrail-root .header-inner {
          max-width: 760px;
          margin: 0 auto;
          padding: 20px 0 16px;
          display: flex;
          align-items: center;
          gap: 14px;
        }
        .obrail-root .logo-rail {
          width: 42px;
          height: 42px;
          background: var(--rail-blue);
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .obrail-root .logo-rail svg { display: block; }
        .obrail-root .site-title {
          font-size: 1.15rem;
          font-weight: 700;
          color: var(--gray-900);
          line-height: 1.2;
        }
        .obrail-root .site-subtitle {
          font-size: 0.8rem;
          color: var(--gray-500);
          margin-top: 2px;
        }
 
        .obrail-root main {
          max-width: 760px;
          margin: 0 auto;
          padding: 40px 24px 80px;
        }
 
        /* ── Intro ── */
        .obrail-root .intro {
          margin-bottom: 36px;
        }
        .obrail-root .intro h1 {
          font-size: 1.75rem;
          font-weight: 800;
          color: var(--gray-900);
          line-height: 1.25;
          margin-bottom: 10px;
        }
        .obrail-root .intro p {
          color: var(--gray-500);
          font-size: 0.97rem;
          max-width: 520px;
        }
 
        /* ── Card ── */
        .obrail-root .card {
          background: var(--white);
          border-radius: var(--radius);
          box-shadow: var(--shadow);
          border: 1px solid var(--gray-100);
          padding: 32px;
          margin-bottom: 28px;
        }
 
        /* ── Formulaire ── */
        .obrail-root .form-group {
          margin-bottom: 20px;
        }
        .obrail-root .form-label {
          display: block;
          font-weight: 600;
          font-size: 0.95rem;
          color: var(--gray-700);
          margin-bottom: 6px;
        }
        .obrail-root .form-hint {
          font-size: 0.83rem;
          color: var(--gray-500);
          margin-bottom: 10px;
          display: block;
        }
        .obrail-root .input-row {
          display: flex;
          gap: 12px;
          align-items: flex-start;
          flex-wrap: wrap;
        }
        .obrail-root .form-input {
          flex: 1;
          min-width: 200px;
          height: 48px;
          padding: 0 16px;
          border: 2px solid var(--gray-300);
          border-radius: var(--radius);
          font-size: 1.05rem;
          color: var(--gray-900);
          background: var(--white);
          transition: border-color 0.15s, box-shadow 0.15s;
          appearance: textfield;
        }
        .obrail-root .form-input::-webkit-inner-spin-button,
        .obrail-root .form-input::-webkit-outer-spin-button { -webkit-appearance: none; }
        .obrail-root .form-input:focus {
          outline: 3px solid var(--rail-blue);
          outline-offset: 2px;
          border-color: var(--rail-blue);
          box-shadow: 0 0 0 4px rgba(21,93,252,0.12);
        }
        .obrail-root .form-input[aria-invalid="true"] {
          border-color: var(--rail-red);
        }
        .obrail-root .form-input[aria-invalid="true"]:focus {
          outline-color: var(--rail-red);
          box-shadow: 0 0 0 4px rgba(192,57,43,0.12);
        }
 
        .obrail-root .btn-submit {
          height: 48px;
          padding: 0 28px;
          background: var(--rail-blue);
          color: var(--white);
          border: none;
          border-radius: var(--radius);
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          white-space: nowrap;
          transition: background 0.15s, transform 0.1s;
          display: inline-flex;
          align-items: center;
          gap: 8px;
        }
        .obrail-root .btn-submit:hover:not(:disabled) { background: var(--rail-dark); }
        .obrail-root .btn-submit:focus-visible {
          outline: 3px solid var(--rail-blue);
          outline-offset: 3px;
        }
        .obrail-root .btn-submit:active:not(:disabled) { transform: scale(0.98); }
        .obrail-root .btn-submit:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }
 
        /* ── Spinner ── */
        .obrail-root .spinner {
          width: 18px;
          height: 18px;
          border: 2.5px solid rgba(255,255,255,0.4);
          border-top-color: var(--white);
          border-radius: 50%;
          animation: obrail-spin 0.7s linear infinite;
          flex-shrink: 0;
        }
        @keyframes obrail-spin { to { transform: rotate(360deg); } }
        @media (prefers-reduced-motion: reduce) {
          .obrail-root .spinner { animation: none; border-top-color: var(--white); }
        }
 
        /* ── Messages ── */
        .obrail-root .field-error {
          margin-top: 8px;
          color: var(--rail-red);
          font-size: 0.87rem;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .obrail-root .field-error svg { flex-shrink: 0; }
 
        /* ── Résultat ── */
        .obrail-root .result-card {
          background: var(--rail-green-bg);
          border: 2px solid var(--rail-green);
          border-radius: var(--radius);
          padding: 28px 32px;
          display: flex;
          align-items: center;
          gap: 24px;
          flex-wrap: wrap;
        }
        .obrail-root .result-icon {
          width: 56px;
          height: 56px;
          background: var(--rail-green);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .obrail-root .result-label {
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--rail-green);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 4px;
        }
        .obrail-root .result-value {
          font-size: 2.4rem;
          font-weight: 800;
          color: var(--gray-900);
          line-height: 1;
        }
        .obrail-root .result-unit {
          font-size: 1rem;
          font-weight: 500;
          color: var(--gray-500);
          margin-left: 4px;
        }
        .obrail-root .result-sub {
          font-size: 0.87rem;
          color: var(--gray-500);
          margin-top: 6px;
        }
 
        .obrail-root .error-card {
          background: var(--rail-red-bg);
          border: 2px solid var(--rail-red);
          border-radius: var(--radius);
          padding: 20px 24px;
          display: flex;
          align-items: flex-start;
          gap: 14px;
        }
        .obrail-root .error-icon {
          width: 40px;
          height: 40px;
          background: var(--rail-red);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          margin-top: 2px;
        }
        .obrail-root .error-title {
          font-weight: 700;
          color: var(--rail-red);
          margin-bottom: 4px;
          font-size: 0.97rem;
        }
        .obrail-root .error-desc {
          font-size: 0.9rem;
          color: var(--gray-700);
        }
 
        /* ── Info bloc ── */
        .obrail-root .info-bloc {
          background: var(--rail-light);
          border-left: 4px solid var(--rail-blue);
          border-radius: 0 var(--radius) var(--radius) 0;
          padding: 16px 20px;
          margin-top: 24px;
          font-size: 0.87rem;
          color: var(--gray-700);
          line-height: 1.6;
        }
        .obrail-root .info-bloc strong { color: var(--rail-dark); }
 
        /* ── Focus visible (scoped) ── */
        .obrail-root :focus-visible {
          outline: 3px solid var(--rail-blue);
          outline-offset: 3px;
          border-radius: 4px;
        }
 
        /* ── Responsive ── */
        @media (max-width: 520px) {
          .obrail-root .card { padding: 22px 16px; }
          .obrail-root .input-row { flex-direction: column; }
          .obrail-root .btn-submit { width: 100%; justify-content: center; }
          .obrail-root .intro h1 { font-size: 1.4rem; }
          .obrail-root .result-value { font-size: 1.9rem; }
        }
      `}</style>

      {/* Skip link RGAA 12.11 */}
      <a href="#main-content" className="skip-link">
        Aller au contenu principal
      </a>

      {/* Zone live pour lecteurs d'écran (RGAA 7.1) */}
      <div
        ref={liveRef}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: "absolute",
          width: "1px",
          height: "1px",
          overflow: "hidden",
          clip: "rect(0,0,0,0)",
          whiteSpace: "nowrap",
        }}
      />

      {/* Contenu principal */}
      <main id="main-content" tabIndex={-1}>
        <div className="intro">
          <h1>Estimation des émissions CO₂</h1>
          <p>
            Saisissez la distance d un trajet ferroviaire pour estimer ses émissions de CO₂ grâce au modèle XGBoost
            ObRail.
          </p>
        </div>

        {/* Formulaire */}
        <div className="card">
          <form onSubmit={handleSubmit} noValidate aria-label="Formulaire d'estimation CO₂">
            <div className="form-group">
              <label htmlFor={inputId} className="form-label">
                Distance du trajet (km)
              </label>
              <span id={descId} className="form-hint">
                Plage acceptée : {MIN_DISTANCE} à {MAX_DISTANCE} km — nombre entier
              </span>
              <div className="input-row">
                <input
                  id={inputId}
                  type="number"
                  inputMode="numeric"
                  className="form-input"
                  value={distance}
                  onChange={(e) => {
                    setDistance(e.target.value);
                    if (status === "error") setStatus("idle");
                  }}
                  min={MIN_DISTANCE}
                  max={MAX_DISTANCE}
                  step={1}
                  aria-describedby={`${descId}${inputInvalid ? ` ${errorId}` : ""}`}
                  aria-invalid={inputInvalid ? "true" : "false"}
                  aria-required="true"
                  autoComplete="off"
                  placeholder={`ex. 800`}
                />
                <button
                  type="submit"
                  className="btn-submit"
                  disabled={status === "loading"}
                  aria-disabled={status === "loading"}
                >
                  {status === "loading" ? (
                    <>
                      <span className="spinner" aria-hidden="true" />
                      Calcul…
                    </>
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                        <path
                          d="M2 8h12M9 4l5 4-5 4"
                          stroke="white"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      Estimer
                    </>
                  )}
                </button>
              </div>

              {/* Erreur champ (RGAA 11.11) */}
              {inputInvalid && (
                <p id={errorId} className="field-error" role="alert">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                    <circle cx="8" cy="8" r="7" stroke="#C0392B" strokeWidth="1.5" />
                    <path d="M8 5v4M8 11v.5" stroke="#C0392B" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                  {validationError}
                </p>
              )}
            </div>

            <div className="info-bloc" role="note">
              <strong>Modèle :</strong> XGBoost entraîné sur 212 trajets ferroviaires européens (R² = 0,971). Valide
              uniquement entre {MIN_DISTANCE} et {MAX_DISTANCE} km. Résultat indicatif.
            </div>
          </form>
        </div>

        {/* Résultat succès */}
        {status === "success" && result && (
          <section aria-label="Résultat de l'estimation" aria-live="polite">
            <div
              className="result-card"
              ref={resultRef}
              tabIndex={-1}
              role="region"
              aria-label={`Émission estimée : ${result.emission_predicted} ${result.emission_unit} pour ${result.distance} km`}
            >
              <div className="result-icon" aria-hidden="true">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                  <path
                    d="M6 15l6 6 10-12"
                    stroke="white"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div className="result-content">
                <div className="result-label">Émissions CO₂ estimées</div>
                <div className="result-value">
                  {result.emission_predicted}
                  <span className="result-unit">{result.emission_unit}</span>
                </div>
                <div className="result-sub">
                  Pour un trajet de <strong>{result.distance} km</strong> — modèle XGBoost ObRail
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Erreur serveur */}
        {status === "error" && !inputInvalid && errorMsg && (
          <section aria-label="Erreur de l'estimation" aria-live="assertive">
            <div className="error-card" role="alert">
              <div className="error-icon" aria-hidden="true">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M10 6v5M10 14v.5" stroke="white" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </div>
              <div>
                <div className="error-title">Impossible d obtenir une estimation</div>
                <div className="error-desc">{errorMsg}</div>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
