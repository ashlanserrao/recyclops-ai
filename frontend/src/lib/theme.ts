// Light, dark or auto (follows the device): a per-browser preference.
// public/theme-init.js applies it before first paint; this keeps it in step afterwards.

import { useSyncExternalStore } from "react";
import { readItem, writeItem } from "@/lib/storage/safe-storage";

export type ThemePreference = "light" | "dark" | "auto";

const KEY = "recyclops.theme";
const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
const listeners = new Set<() => void>();

function read(): ThemePreference {
  const stored = readItem("local", KEY);
  return stored === "light" || stored === "dark" ? stored : "auto";
}

let preference = read();

const resolveTheme = (pref: ThemePreference): "light" | "dark" =>
  pref === "auto" ? (darkQuery.matches ? "dark" : "light") : pref;

/** Sets data-theme and the browser bar colour; crossfades only when the user switches. */
function apply(crossfade: boolean) {
  const root = document.documentElement;
  const fade = crossfade && !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (fade) root.classList.add("theme-switching");
  root.dataset.theme = resolveTheme(preference);
  const bar = getComputedStyle(root).getPropertyValue("--browser-bar").trim();
  if (bar) document.querySelector('meta[name="theme-color"]')?.setAttribute("content", bar);
  if (fade) window.setTimeout(() => root.classList.remove("theme-switching"), 200);
  for (const listener of listeners) listener();
}

export function setThemePreference(next: ThemePreference) {
  preference = next;
  writeItem("local", KEY, next);
  apply(true);
}

/** Call once at start-up: syncs the browser bar and follows the device while on auto. */
export function initTheme() {
  apply(false);
  darkQuery.addEventListener("change", () => {
    if (preference === "auto") apply(true);
  });
}

const subscribe = (listener: () => void) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

export function useTheme() {
  const current = useSyncExternalStore(subscribe, () => preference);
  return { preference: current, setPreference: setThemePreference };
}
