// One activity's advice: what to do, why, and how much it helps. Used by the day plan and the Ask answer.

import { CircleAlert, CircleCheck, CircleHelp, Clock } from "lucide-react";
import { BandBadge, SourceBadge } from "@/components/badges";
import type { DecisionOut } from "@/lib/api/types";
import { activityLine, decisionHeadline, type Tone } from "@/lib/labels";
import { cn } from "@/lib/utils";

const TONES: Record<Tone, { icon: typeof Clock; className: string }> = {
  success: { icon: CircleCheck, className: "border-success/30 bg-success-soft text-success" },
  warning: { icon: Clock, className: "border-warning/30 bg-warning-soft text-warning" },
  danger: { icon: CircleAlert, className: "border-danger/30 bg-danger-soft text-danger" },
  neutral: { icon: CircleHelp, className: "border-border bg-surface-soft text-muted-foreground" },
};

/** A status in words with an icon, never colour alone. */
export function ToneChip({ tone, children }: { tone: Tone; children: string }) {
  const { icon: Icon, className } = TONES[tone];
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-sm font-semibold", className)}>
      <Icon className="size-4" aria-hidden="true" />
      {children}
    </span>
  );
}

export function DecisionCard({ decision, aiWorded }: { decision: DecisionOut; aiWorded: boolean }) {
  const headline = decisionHeadline(decision);
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-medium">{activityLine(decision.activity)}</p>
        {decision.band_now && (
          <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
            air then <BandBadge band={decision.band_now} />
          </span>
        )}
      </div>
      <ToneChip tone={headline.tone}>{headline.text}</ToneChip>
      {decision.impact && <p className="font-medium">{decision.impact}</p>}
      <p className="text-sm text-muted-foreground">
        {decision.why}
        {aiWorded && <> <SourceBadge source="ai" /></>}
      </p>
    </div>
  );
}
