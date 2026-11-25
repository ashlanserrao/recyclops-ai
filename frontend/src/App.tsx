import { Wind } from "lucide-react";
import { useState } from "react";
import { ThemeToggle } from "@/components/theme-toggle";
import { AskPanel } from "@/features/ask/ask-panel";
import { PlanSection } from "@/features/plan/plan-section";
import { type PlanState, usePlan } from "@/features/plan/use-plan";
import { SetupPanel } from "@/features/setup/setup-panel";
import type { FieldError } from "@/lib/api/types";
import { BAND_LABELS } from "@/lib/format";
import type { Profile } from "@/lib/household";
import { loadProfile, saveProfile } from "@/lib/storage/profile";

const NO_ERRORS: FieldError[] = [];

/** What a screen reader hears as the plan changes; failures use their own alert instead. */
function announcement(state: PlanState): string {
  if (state.status === "loading") return "Planning the day…";
  if (state.status !== "ready") return "";
  const { city, air } = state.plan;
  const aqi = air.aqi ? ` AQI ${air.aqi.value}, ${BAND_LABELS[air.aqi.band]}.` : " No measured AQI nearby.";
  return `Plan ready for ${city ?? "your location"}.${aqi}`;
}

/** The page: the household (saved in this browser), then today's air and plan for it. */
export default function App() {
  const [profile, setProfile] = useState<Profile | null>(loadProfile);
  const [editing, setEditing] = useState(profile === null);
  const { state, refresh } = usePlan(profile);

  // The server checks every value; anything it rejects reopens the form on the fields it names.
  const fieldErrors = state.status === "failed" && state.error.fields.length ? state.error.fields : NO_ERRORS;
  const formOpen = editing || fieldErrors !== NO_ERRORS;

  const save = (next: Profile) => {
    saveProfile(next);
    setProfile(next);
    setEditing(false);
  };

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
        <SetupPanel profile={profile} editing={formOpen} serverErrors={fieldErrors}
          onEdit={() => setEditing(true)} onSave={save}
          onCancel={fieldErrors === NO_ERRORS ? () => setEditing(false) : undefined} />
        {!formOpen && <PlanSection state={state} onRefresh={refresh} />}
        {!formOpen && profile && <AskPanel profile={profile} />}
      </main>
      <footer className="mx-auto max-w-5xl px-4 pb-8 text-xs text-muted-foreground">
        Air data: monitoring stations via OpenAQ (CPCB network) and the Open-Meteo forecast (CAMS).
        Advice is computed by fixed rules from that data; the AI only words it.
      </footer>
      {/* One polite announcer for results that appear without a page change. */}
      <p role="status" aria-live="polite" className="sr-only">{announcement(state)}</p>
    </>
  );
}
