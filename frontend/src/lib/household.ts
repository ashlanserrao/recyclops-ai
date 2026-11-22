// The household as the setup form edits it, and the checks the browser can make before sending it.
// The server validates everything again (ranges, ids, times); its field paths are the ones used here,
// so one error map serves both: "household.members.0.age" names the same input either way.

import type { Activity, Commute, FieldError, Household, Member } from "@/lib/api/types";

export const MAX_MEMBERS = 5;
export const MAX_ACTIVITIES = 5;

/** Where plans are made for: a listed city, or the device's position rounded to about a kilometre. */
export type Place = { source: "city" | "device"; name: string | null; lat: number; lon: number };

export type Profile = { place: Place; household: Household };

export const newActivity = (): Activity => ({ kind: "walk", start: "07:00", duration_min: 30, intensity: "light" });

export const newCommute = (): Commute =>
  ({ mode: "bus", one_way_km: 5, days_per_week: 5, departs: "08:30", walking_leg_min: 0 });

/** A blank member with an id no one else in the household has (ids only need to be unique within it). */
export function newMember(members: Member[]): Member {
  const taken = new Set(members.map((member) => member.id));
  let n = members.length + 1;
  while (taken.has(`m${n}`)) n += 1;
  return { id: `m${n}`, name: "", type: "adult", age: Number.NaN, health_flags: [], activities: [], commute: null };
}

export const newHousehold = (): Household => ({
  home: { has_purifier: false, purifier_room_m2: null, cooking_fuel: "lpg", faces_main_road: false },
  members: [newMember([])],
});

/** Blank or unreadable entries, worded for people; the server checks ranges and the rest. */
export function missingFields({ place, household }: { place: Place | null; household: Household }): FieldError[] {
  const errors: FieldError[] = [];
  const need = (blank: boolean, field: string, message: string) => blank && errors.push({ field, message });
  const noNumber = (value: number | null | undefined) => value == null || Number.isNaN(value);

  need(place === null, "location", "Choose a city or use your location.");
  household.members.forEach((member, i) => {
    const at = `household.members.${i}`;
    need(!member.name.trim(), `${at}.name`, "Enter a name or nickname.");
    need(noNumber(member.age), `${at}.age`, "Enter an age in years.");
    member.activities.forEach((activity, j) => {
      need(!activity.start, `${at}.activities.${j}.start`, "Enter a start time.");
      need(noNumber(activity.duration_min), `${at}.activities.${j}.duration_min`, "Enter how many minutes.");
    });
    const commute = member.commute;
    if (commute) {
      need(noNumber(commute.one_way_km), `${at}.commute.one_way_km`, "Enter the distance one way.");
      need(noNumber(commute.days_per_week), `${at}.commute.days_per_week`, "Enter how many days a week.");
      need(!commute.departs, `${at}.commute.departs`, "Enter when they usually leave.");
      need(noNumber(commute.walking_leg_min), `${at}.commute.walking_leg_min`, "Enter the minutes, or 0.");
    }
  });
  return errors;
}

/** Field path -> message; when the server sends two for one field, the first one is shown. */
export function errorMap(fields: FieldError[]): Record<string, string> {
  const map: Record<string, string> = {};
  for (const { field, message } of fields) map[field] ??= message;
  return map;
}

// Mirrors the API's Location bounds (schemas.py), so the browser can explain the problem in words.
const INDIA = { lat: [6, 37.6], lon: [68, 97.5] } as const;

/** A device position as a Place: rounded to 2 decimals (about 1 km), which is all a station lookup needs. */
export function devicePlace(lat: number, lon: number): Place | null {
  const inside = lat >= INDIA.lat[0] && lat <= INDIA.lat[1] && lon >= INDIA.lon[0] && lon <= INDIA.lon[1];
  const round = (value: number) => Math.round(value * 100) / 100;
  return inside ? { source: "device", name: null, lat: round(lat), lon: round(lon) } : null;
}

/** "Aarav (8), Dadi (68)": who the plan is for, in one line. */
export const membersLine = (household: Household) =>
  household.members.map((member) => `${member.name} (${member.age})`).join(", ");
