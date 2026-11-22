/// <reference types="vitest/config" />
import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(import.meta.dirname, "src") } },
  // In development the API runs separately: uvicorn recyclops.api.main:app --port 8000
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
  build: { outDir: "dist", emptyOutDir: true },
  // Unit tests cover pure logic (src/lib); the UI is covered end to end by Playwright.
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
