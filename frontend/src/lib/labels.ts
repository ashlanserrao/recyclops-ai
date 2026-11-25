// The words for the API's codes, in one place so the form and the plan say the same thing.

import type {
  Activity, ActivityKind, Alternative, CommuteMode, CookingFuel, DecisionOut, HealthFlag, HomeAction, Intensity, MemberType,
  Verdict,
} from "@/lib/api/types";
import { clock, clockTime } from "@/lib/format";

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

export const HOME_ACTIONS: Record<HomeAction, string> = {
  keep_windows_shut: "Keep the windows shut",
  air_out_in_best_window: "Air the house out briefly",
  close_road_side: "Keep road-side windows closed",
  run_purifier: "Run the purifier",
  consider_purifier: "Consider an air purifier",
  switch_from_biomass: "Move away from smoky cooking fuel",
  use_kitchen_exhaust: "Use the kitchen chimney or exhaust",
  wet_mop: "Wet-mop instead of sweeping",
  no_incense_or_coils: "Skip incense and mosquito coils",
};

export const ALTERNATIVES: Record<Alternative, string> = {
  metro: "Take the metro",
  bus: "Take the bus",
  carpool: "Carpool with two others",
};

export type Tone = "success" | "warning" | "danger" | "neutral";

/** The decision in a few words, and how urgent it looks: "Move to 1 pm", warning. */
export function decisionHeadline(decision: DecisionOut): { text: string; tone: Tone } {
  switch (decision.action) {
    case "keep":
      return { text: "Go ahead as planned", tone: "success" };
    case "move":
      return { text: decision.new_start ? `Move to ${clock(decision.new_start)}` : "Move to a cleaner time", tone: "warning" };
    case "shorten":
      return { text: `Shorten to ${decision.new_duration_min} min`, tone: "warning" };
    case "indoor":
      return { text: "Do it indoors today", tone: "danger" };
    case "no_data":
      return { text: "No forecast for this time yet", tone: "neutral" };
  }
}

/** The answer to "Can we...?", in a few words. */
export const VERDICTS: Record<Verdict, { text: string; tone: Tone }> = {
  yes: { text: "Yes, go ahead", tone: "success" },
  better_time: { text: "Better at another time", tone: "warning" },
  shorter: { text: "Yes, but keep it shorter", tone: "warning" },
  indoors: { text: "Better indoors today", tone: "danger" },
  unknown: { text: "Can't say yet", tone: "neutral" },
};

/** "Outdoor play at 5 pm, 60 min": the activity as the person entered it. */
export const activityLine = ({ kind, start, duration_min }: Activity) =>
  `${ACTIVITY_KINDS[kind]} at ${clockTime(start)}, ${duration_min} min`;

/** [value, label] pairs in the order written above, for <option> lists. */
export const options = <K extends string>(labels: Record<K, string>) => Object.entries(labels) as [K, string][];
