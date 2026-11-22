// The words for the API's codes, in one place so the form and the plan say the same thing.

import type { ActivityKind, CommuteMode, CookingFuel, HealthFlag, Intensity, MemberType } from "@/lib/api/types";

export const MEMBER_TYPES: Record<MemberType, string> = {
  child: "Child",
  student: "Student",
  adult: "Adult",
  senior: "Senior",
};

export const HEALTH_FLAGS: Record<HealthFlag, string> = {
  respiratory: "Asthma or another breathing condition",
  heart: "Heart condition",
  pregnancy: "Pregnant",
};

export const ACTIVITY_KINDS: Record<ActivityKind, string> = {
  walk: "Walk",
  play: "Outdoor play",
  sport: "Sport",
  exercise: "Exercise or run",
  errand: "Errands",
  other: "Something else outdoors",
};

export const INTENSITIES: Record<Intensity, string> = {
  light: "Light: strolling",
  moderate: "Moderate: brisk, play",
  high: "Hard: running, matches",
};

export const COMMUTE_MODES: Record<CommuteMode, string> = {
  car: "Car",
  two_wheeler: "Two-wheeler",
  auto: "Auto-rickshaw",
  bus: "Bus",
  metro: "Metro",
  walk: "Walking",
  cycle: "Cycle",
};

export const COOKING_FUELS: Record<CookingFuel, string> = {
  lpg: "LPG cylinder",
  png: "Piped gas (PNG)",
  electric: "Electric or induction",
  biomass: "Wood, coal, dung or kerosene",
};

/** [value, label] pairs in the order written above, for <option> lists. */
export const options = <K extends string>(labels: Record<K, string>) => Object.entries(labels) as [K, string][];
