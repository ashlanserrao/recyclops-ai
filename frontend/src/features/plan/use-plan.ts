// Today's plan for the saved household: fetched whenever the profile changes, or on "Refresh".
// A newer request aborts the older one, so a slow answer for an old household can never overwrite a new one.

import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api/client";
import type { PlanOut } from "@/lib/api/types";
import type { Profile } from "@/lib/household";

export type PlanState =
  | { status: "idle" }
  | { status: "loading"; previous: PlanOut | null }
  | { status: "ready"; plan: PlanOut; profile: Profile }
  | { status: "failed"; error: ApiError };

export function usePlan(profile: Profile | null) {
  const [state, setState] = useState<PlanState>({ status: "idle" });
  const [attempt, setAttempt] = useState(0);

  // biome-ignore lint/correctness/useExhaustiveDependencies: `attempt` is the refresh trigger; it isn't read inside.
  useEffect(() => {
    if (!profile) {
      setState({ status: "idle" });
      return;
    }
    const controller = new AbortController();
    // A refresh keeps the current plan on screen; a changed household doesn't show the old one's plan.
    setState((current) => ({
      status: "loading", previous: current.status === "ready" && current.profile === profile ? current.plan : null,
    }));
    const { place, household } = profile;
    api.plan({ location: { lat: place.lat, lon: place.lon }, household }, controller.signal).then(
      (plan) => setState({ status: "ready", plan, profile }),
      (error: unknown) => {
        if (controller.signal.aborted) return;
        setState({ status: "failed", error: error instanceof ApiError ? error : new ApiError(String(error)) });
      },
    );
    return () => controller.abort();
  }, [profile, attempt]);

  const refresh = useCallback(() => setAttempt((n) => n + 1), []);
  return { state, refresh };
}
