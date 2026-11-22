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

/** 5 pm, 6:30 am, from a time of day ("17:00" or "17:00:00"). */
export function clockTime(hhmm: string): string {
  const [hours = 0, minutes = 0] = hhmm.slice(0, 5).split(":").map(Number);
  const hour = hours % 12 || 12;
  const suffix = hours < 12 ? "am" : "pm";
  return minutes ? `${hour}:${String(minutes).padStart(2, "0")} ${suffix}` : `${hour} ${suffix}`;
}

/** 5 pm, 6:30 am: the time as shown in India, from an ISO string with its offset (not the browser's zone). */
export const clock = (iso: string) => clockTime(iso.slice(11, 16));

/** "Wed 25 Nov", from "2026-11-25" (a calendar date, read without time zones). */
export function day(isoDate: string): string {
  const [year = 0, month = 1, date = 1] = isoDate.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, date))
    .toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" });
}

/** "25 Nov, 1 pm": the reading's own time, never "now". */
export function stamp(iso: string): string {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const month = months[Number(iso.slice(5, 7)) - 1] ?? "";
  return `${Number(iso.slice(8, 10))} ${month}, ${clock(iso)}`;
}
