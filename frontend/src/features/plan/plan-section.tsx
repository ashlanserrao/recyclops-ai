// The plan area: loading, a failure with a way forward, or the plan itself.
// Field errors aren't shown here: they reopen the household form, on the inputs they name.

import { LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { AirPanel } from "@/features/plan/air-panel";
import { DayPlan } from "@/features/plan/day-plan";
import type { PlanState } from "@/features/plan/use-plan";

export function PlanSection({ state, onRefresh }: { state: PlanState; onRefresh: () => void }) {
  if (state.status === "idle") return null;

  if (state.status === "failed") {
    if (state.error.fields.length) return null;
    return (
      <div role="alert" className="space-y-3 rounded-xl border border-danger bg-danger-soft p-5">
        <p className="font-semibold">{state.error.message}</p>
        <Button variant="outline" onClick={onRefresh}>Try again</Button>
      </div>
    );
  }

  const plan = state.status === "ready" ? state.plan : state.previous;
  if (!plan) return <Loading />;
  // While refreshing, the last plan stays on screen (marked busy) instead of blinking away.
  return (
    <div aria-busy={state.status === "loading"} className="space-y-6">
      <AirPanel plan={plan} onRefresh={onRefresh} refreshing={state.status === "loading"} />
      <DayPlan plan={plan} />
    </div>
  );
}

// The free API host sleeps when idle, and its first reply can take up to a minute: say so instead of seeming stuck.
const SLOW_AFTER_MS = 6000;

function Loading() {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), SLOW_AFTER_MS);
    return () => clearTimeout(timer);
  }, []);
  return (
    <div aria-busy="true" className="flex items-center gap-3 rounded-xl border bg-card p-5 text-sm">
      <LoaderCircle className="size-5 shrink-0 animate-spin text-primary-ink" aria-hidden="true" />
      <p>
        Checking the air near you and planning the day. This usually takes a few seconds.
        {slow && " The server is starting up after a quiet spell; the first plan can take up to a minute."}
      </p>
    </div>
  );
}
