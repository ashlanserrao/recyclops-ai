// Readable names for the generated API types (generated.ts: never edit it; run `npm run gen:types`).

import type { components } from "@/lib/api/generated";

type Schemas = components["schemas"];

export type Activity = Schemas["Activity"];
export type ActivityKind = Schemas["ActivityKind"];
export type AirOut = Schemas["AirOut"];
export type AskOut = Schemas["AskOut"];
export type AskRequest = Schemas["AskRequest"];
export type Band = Schemas["Band"];
export type City = Schemas["CityOut"];
export type Commute = Schemas["Commute"];
export type CommuteMode = Schemas["CommuteMode"];
export type CookingFuel = Schemas["CookingFuel"];
export type DecisionOut = Schemas["DecisionOut"];
export type HealthFlag = Schemas["HealthFlag"];
export type Home = Schemas["Home"];
export type HomeAdviceOut = Schemas["HomeAdviceOut"];
export type Household = Schemas["Household"];
export type Intensity = Schemas["Intensity"];
export type Location = Schemas["Location"];
export type Member = Schemas["Member"];
export type MemberPlanOut = Schemas["MemberPlanOut"];
export type MemberType = Schemas["MemberType"];
export type PlanOut = Schemas["PlanOut"];
export type PlanRequest = Schemas["PlanRequest"];
export type SwapOut = Schemas["SwapOut"];
export type Verdict = Schemas["Verdict"];
export type WindowOut = Schemas["WindowOut"];

/** The server's error shape: {error, fields: [{field, message}]}. */
export type FieldError = { field: string; message: string };
