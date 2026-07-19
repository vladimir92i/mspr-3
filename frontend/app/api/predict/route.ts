import { NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "http://localhost:8000";
const API_KEY = process.env.API_KEY ?? "obrail-local-api-key";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const distance = url.searchParams.get("distance");

  if (!distance) {
    return NextResponse.json({ detail: "Distance manquante." }, { status: 400 });
  }

  const response = await fetch(`${API_URL}/api/ml/predict?distance=${encodeURIComponent(distance)}`, {
    method: "GET",
    headers: {
      "x-api-key": API_KEY,
    },
  });

  const payload = await response.json().catch(() => ({}));

  return NextResponse.json(payload, { status: response.status });
}
