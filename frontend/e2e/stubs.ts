// API stubs for the browser tests: the backend's own saved responses (tests/frontend_fixtures.py checks
// they still match the API), so the page is tested on real shapes and wording without live air data or AI.

import { readFileSync } from "node:fs";
import type { Page } from "@playwright/test";

const fixture = (name: string) => JSON.parse(readFileSync(new URL(`./fixtures/${name}`, import.meta.url), "utf-8"));

export const DELHI_PLAN = fixture("plan-delhi.json");
export const DELHI_ASK: { by_ai: object; needs_form: object; by_form: object } = fixture("ask-delhi.json");

export const servePlan = (page: Page, plan: object = DELHI_PLAN) =>
  page.route("**/api/plan", (route) => route.fulfill({ json: plan }));

/** Typed questions get `forQuestion` (read by AI, or "needs the form"); the form gets the form's answer. */
export const serveAsk = (page: Page, forQuestion: object = DELHI_ASK.by_ai) =>
  page.route("**/api/ask", (route) =>
    route.fulfill({ json: route.request().postDataJSON().form ? DELHI_ASK.by_form : forQuestion }));
