// Three example households, one click each, so anyone can see a full plan without typing.
// They match the spec's golden scenarios (plans G1-G3; backend tests/golden.py) but get live air data.

import type { Profile } from "@/lib/household";

export type Demo = { id: string; label: string; detail: string; profile: Profile };

export const DEMOS: Demo[] = [
  {
    id: "delhi",
    label: "Delhi family",
    detail: "A child who plays outside, a grandmother with asthma, a parent who drives to work",
    profile: {
      place: { source: "city", name: "Delhi", lat: 28.6139, lon: 77.209 },
      household: {
        home: { has_purifier: false, purifier_room_m2: null, cooking_fuel: "lpg", faces_main_road: true },
        members: [
          { id: "aarav", name: "Aarav", type: "child", age: 8, health_flags: [], commute: null,
            activities: [{ kind: "play", start: "17:00", duration_min: 60, intensity: "moderate" }] },
          { id: "dadi", name: "Dadi", type: "senior", age: 68, health_flags: ["respiratory"], commute: null,
            activities: [{ kind: "walk", start: "07:00", duration_min: 30, intensity: "light" }] },
          { id: "priya", name: "Priya", type: "adult", age: 38, health_flags: [], activities: [],
            commute: { mode: "car", one_way_km: 15, days_per_week: 5, departs: "08:30", walking_leg_min: 0 } },
        ],
      },
    },
  },
  {
    id: "mumbai",
    label: "Mumbai senior",
    detail: "A 70-year-old with a heart condition who walks early each morning",
    profile: {
      place: { source: "city", name: "Mumbai", lat: 19.076, lon: 72.8777 },
      household: {
        home: { has_purifier: true, purifier_room_m2: 12, cooking_fuel: "png", faces_main_road: false },
        members: [
          { id: "nana", name: "Nana", type: "senior", age: 70, health_flags: ["heart"], commute: null,
            activities: [{ kind: "walk", start: "06:30", duration_min: 30, intensity: "light" }] },
        ],
      },
    },
  },
  {
    id: "kolkata",
    label: "Kolkata student",
    detail: "A 19-year-old who takes the bus to college and plays football in the evening",
    profile: {
      place: { source: "city", name: "Kolkata", lat: 22.5726, lon: 88.3639 },
      household: {
        home: { has_purifier: false, purifier_room_m2: null, cooking_fuel: "lpg", faces_main_road: false },
        members: [
          { id: "rohan", name: "Rohan", type: "student", age: 19, health_flags: [],
            activities: [{ kind: "sport", start: "17:00", duration_min: 90, intensity: "high" }],
            commute: { mode: "bus", one_way_km: 10, days_per_week: 5, departs: "08:30", walking_leg_min: 15 } },
        ],
      },
    },
  },
];
