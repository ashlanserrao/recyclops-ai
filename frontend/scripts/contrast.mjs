// WCAG AA check for every text/background token pair, in both themes, including the six CPCB
// band colours. Reads the tokens straight from src/index.css, prints a table, exits 1 on a failure.
// Usage: npm run contrast

import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/index.css", import.meta.url), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
const blocks = [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(([, selector, body]) => ({
  selector: selector.split(";").pop().trim().replace(/\s+/g, " "),
  vars: Object.fromEntries([...body.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map(([, k, v]) => [k, v.trim()])),
}));
const merge = (match) => Object.assign({}, ...blocks.filter((b) => match(b.selector)).map((b) => b.vars));
const light = merge((s) => s === ":root");
const themes = { light, dark: { ...light, ...merge((s) => s === ':root[data-theme="dark"]') } };

const resolve = (vars, value, depth = 0) => {
  const ref = value?.match(/^var\((--[\w-]+)\)$/);
  return ref && depth < 10 ? resolve(vars, vars[ref[1]], depth + 1) : value;
};
const luminance = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (a, b) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};

// [foreground, background, minimum, what it is]
const SURFACES = ["--bg-canvas", "--bg-surface", "--bg-surface-soft"];
const BANDS = ["good", "satisfactory", "moderate", "poor", "very-poor", "severe"];
const PAIRS = [
  ...["--text-primary", "--text-secondary", "--text-tertiary"].flatMap((fg) => SURFACES.map((bg) => [fg, bg, 4.5, "text"])),
  ...SURFACES.map((bg) => ["--accent-ink", bg, 4.5, "accent as text"]),
  ["--accent-ink", "--accent-soft", 4.5, "ink on accent tint"],
  ["--on-accent", "--accent", 4.5, "filled button"],
  ["--on-accent", "--accent-hover", 4.5, "filled button, hover"],
  ...SURFACES.map((bg) => ["--border-strong", bg, 3, "field edge"]),
  ["--accent", "--bg-surface", 3, "focus ring (light)"],
  ...["warning", "danger", "success"].flatMap((name) => [
    [`--${name}`, `--${name}-soft`, 4.5, `${name} badge`],
    [`--${name}`, "--bg-surface", 4.5, `${name} text`],
    [`--${name}`, "--bg-surface-soft", 4.5, `${name} text on a soft row`],
    ["--text-primary", `--${name}-soft`, 4.5, `body text in a ${name} box`],
  ]),
  ["--ai", "--ai-soft", 4.5, "AI text"],
  ["--ai", "--ai-tint", 4.5, "AI chip"],
  ["--ai", "--bg-surface", 4.5, "AI text on card"],
  ...BANDS.flatMap((band) => [
    [`--aqi-${band}`, `--aqi-${band}-soft`, 4.5, `${band} band text on its fill`],
    [`--aqi-${band}`, "--bg-surface", 4.5, `${band} band text on card`],
  ]),
];

let failures = 0;
const rows = [];
for (const [theme, vars] of Object.entries(themes)) {
  for (const [fg, bg, min, what] of PAIRS) {
    const [a, b] = [resolve(vars, vars[fg]), resolve(vars, vars[bg])];
    if (!/^#[0-9a-f]{6}$/i.test(a ?? "") || !/^#[0-9a-f]{6}$/i.test(b ?? "")) {
      console.error(`Can't check ${fg} on ${bg} (${theme}): ${a} / ${b}`);
      failures++;
      continue;
    }
    const r = ratio(a, b);
    if (r < min) failures++;
    rows.push([theme, what, `${fg} on ${bg}`, `${a} / ${b}`, r.toFixed(2), min, r >= min ? "pass" : "FAIL"]);
  }
}

const head = ["theme", "use", "pair", "colours", "ratio", "min", "result"];
const widths = head.map((h, i) => Math.max(h.length, ...rows.map((row) => String(row[i]).length)));
const line = (cells) => cells.map((c, i) => String(c).padEnd(widths[i])).join("  ");
console.log(line(head));
console.log(widths.map((w) => "-".repeat(w)).join("  "));
for (const row of rows) console.log(line(row));
console.log(`\n${failures ? `${failures} pair(s) below AA` : "Every text and control pair meets WCAG AA"} (${rows.length} checked).`);
process.exit(failures ? 1 : 0);
