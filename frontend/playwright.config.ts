// End-to-end check of the built app, served by the real backend with every external key blanked.
// Run `npm run build` first. Uses the installed Chrome, so there's no browser download.

import { existsSync } from "node:fs";
import { defineConfig } from "@playwright/test";

if (!existsSync("dist/index.html")) throw new Error("No frontend build: run npm run build first.");

// Not 8000, so a dev server you already have running is never reused or disturbed.
const PORT = 8010;
// The project venv locally (plain `python` on Windows may be another install); CI's python otherwise.
// Backslashes because Windows' shell reads "/" as an option switch.
const PYTHON = process.env.PYTHON ?? (existsSync("../venv/Scripts/python.exe") ? "venv\\Scripts\\python.exe" : "python");

export default defineConfig({
  testDir: "e2e",
  use: { baseURL: `http://127.0.0.1:${PORT}`, channel: "chrome" },
  webServer: {
    command: `${PYTHON} -m uvicorn recyclops.api.main:app --port ${PORT}`,
    cwd: "..",
    url: `http://127.0.0.1:${PORT}/api/health`,
    reuseExistingServer: false,
    // Empty keys win over .env, so an end-to-end run never calls a real AQI source or AI provider.
    env: { OPENAQ_API_KEY: "", GROQ_API_KEY: "", OPENAI_API_KEY: "" },
  },
});
