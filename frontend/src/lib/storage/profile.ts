// The household and place, saved in this browser only (the server keeps nothing between requests).
// The key carries a version, so a later shape change can migrate or drop old data instead of misreading it.

import type { Profile } from "@/lib/household";
import { readItem, writeItem } from "@/lib/storage/safe-storage";

export const PROFILE_KEY = "recyclops.profile.v1";

const isObject = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null;

/** Enough of a shape check to render the form safely; the server validates the rest on every plan. */
function isProfile(value: unknown): value is Profile {
  if (!isObject(value) || !isObject(value.place) || !isObject(value.household)) return false;
  const { place, household } = value;
  return (place.source === "city" || place.source === "device")
    && typeof place.lat === "number" && typeof place.lon === "number"
    && isObject(household.home) && Array.isArray(household.members) && household.members.length > 0
    && household.members.every((member) => isObject(member) && typeof member.id === "string"
      && typeof member.name === "string" && Array.isArray(member.activities) && Array.isArray(member.health_flags));
}

/** The saved profile, or null when there is none or it can't be read (blocked storage, edited by hand). */
export function loadProfile(): Profile | null {
  const raw = readItem("local", PROFILE_KEY);
  if (!raw) return null;
  try {
    const value: unknown = JSON.parse(raw);
    return isProfile(value) ? value : null;
  } catch {
    return null;
  }
}

export const saveProfile = (profile: Profile) => writeItem("local", PROFILE_KEY, JSON.stringify(profile));
