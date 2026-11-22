// Words and formats shown to people: one place, so every screen says the same thing.

import type { Band } from "@/lib/api/types";

export const BAND_LABELS: Record<Band, string> = {
  good: "Good",
  satisfactory: "Satisfactory",
  moderate: "Moderate",
  poor: "Poor",
  very_poor: "Very poor",
  severe: "Severe",
};

/** The CSS token suffix for a band: `very_poor` -> `very-poor` (classes like bg-aqi-very-poor-soft). */
export const bandToken = (band: Band) => band.replace("_", "-");

/** 5 pm, 6:30 am: the time as shown in India, from an ISO string with its offset. */
export function clock(iso: string): string {
  const [hours, minutes] = iso.slice(11, 16).split(":").map(Number);
  const hour = (hours ?? 0) % 12 || 12;
  const suffix = (hours ?? 0) < 12 ? "am" : "pm";
  return minutes ? `${hour}:${String(minutes).padStart(2, "0")} ${suffix}` : `${hour} ${suffix}`;
}

/** "25 Nov, 1 pm": the reading's own time, never "now". */
export function stamp(iso: string): string {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const month = months[Number(iso.slice(5, 7)) - 1] ?? "";
  return `${Number(iso.slice(8, 10))} ${month}, ${clock(iso)}`;
}
