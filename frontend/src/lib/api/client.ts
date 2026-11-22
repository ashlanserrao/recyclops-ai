// The one way to the backend: same-origin paths only (the CSP allows nothing else; Vercel forwards
// /api/* to the API). Errors carry the server's plain-language message and per-field problems.

import type { AskOut, AskRequest, FieldError, PlanOut, PlanRequest } from "@/lib/api/types";

export class ApiError extends Error {
  readonly fields: FieldError[];
  readonly status: number;

  constructor(message: string, status = 0, fields: FieldError[] = []) {
    super(message);
    this.status = status;
    this.fields = fields;
  }
}

export const OFFLINE_MESSAGE = "Can't reach the planner right now. Your household is saved in this browser. Check your connection and try again.";
const UNKNOWN_MESSAGE = "That didn't work. Your household is saved in this browser. Please try again.";

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(OFFLINE_MESSAGE);
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(body.error || UNKNOWN_MESSAGE, response.status, Array.isArray(body.fields) ? body.fields : []);
  }
  return body as T;
}

const post = <T>(path: string, body: unknown, signal?: AbortSignal) =>
  request<T>(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal });

export const api = {
  /** Today's plan from live air data; the explanations may be AI-worded (`ai_used`). */
  plan: (body: PlanRequest, signal?: AbortSignal) => post<PlanOut>("/api/plan", body, signal),
  /** "Can we...?" for one member and one activity: a typed question or the form. */
  ask: (body: AskRequest, signal?: AbortSignal) => post<AskOut>("/api/ask", body, signal),
};
