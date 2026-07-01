// src/lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format duration from minutes to human-readable format
 * @param minutes - Duration in minutes
 * @returns Formatted string like "2h 15m"
 */
export function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m.toString().padStart(2, "0")}m`;
}

/**
 * Calculate CO2 emissions for a flight on the same distance
 * Avion ≈ 255 gCO₂/km, train ≈ emission kg total
 * @param distance - Distance in km
 * @returns CO2 emissions in kg
 */
export function co2Avion(distance: number): number {
  return Math.round(distance * 0.255); // 255 gCO₂/km → kg
}

export function extractHour(time: string | null): number {
  if (!time || time === "—") return 0;
  const hour = Number.parseInt(time.split(":")[0], 10);
  return Number.isNaN(hour) ? 0 : hour;
}

export function isNightTrain(departureTime: string | null): boolean {
  if (!departureTime) return false;
  const hour = extractHour(departureTime);
  return hour >= 22 || hour < 6;
}
