import { Wind } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

/** The page shell: skip link, header, the planner (built section by section), and the data sources. */
export default function App() {
  return (
    <>
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-surface focus:px-4 focus:py-2">
        Skip to content
      </a>
      <header className="border-b bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <p className="flex items-center gap-2 font-semibold">
            <Wind className="size-5 text-primary-ink" aria-hidden="true" />
            recyclops-ai
            <span className="hidden text-sm font-normal text-muted-foreground sm:inline">clean-air day planner</span>
          </p>
          <ThemeToggle />
        </div>
      </header>
      <main id="main" className="mx-auto max-w-5xl space-y-6 px-4 py-6">
        <h1 className="text-2xl">Plan your household's day around the air</h1>
      </main>
      <footer className="mx-auto max-w-5xl px-4 pb-8 text-xs text-muted-foreground">
        Air data: monitoring stations via OpenAQ (CPCB network) and the Open-Meteo forecast (CAMS).
        Advice is computed by fixed rules from that data; the AI only words it.
      </footer>
    </>
  );
}
