// Small labels that always carry a word, never colour alone.

import { Cpu, Gauge, Sparkles, TrendingUp } from "lucide-react";
import type { Band } from "@/lib/api/types";
import { BAND_LABELS, bandToken } from "@/lib/format";
import { cn } from "@/lib/utils";

// Spelled out so Tailwind sees every class it must generate.
const BAND_CLASSES: Record<Band, string> = {
  good: "border-aqi-good-border bg-aqi-good-soft text-aqi-good",
  satisfactory: "border-aqi-satisfactory-border bg-aqi-satisfactory-soft text-aqi-satisfactory",
  moderate: "border-aqi-moderate-border bg-aqi-moderate-soft text-aqi-moderate",
  poor: "border-aqi-poor-border bg-aqi-poor-soft text-aqi-poor",
  very_poor: "border-aqi-very-poor-border bg-aqi-very-poor-soft text-aqi-very-poor",
  severe: "border-aqi-severe-border bg-aqi-severe-soft text-aqi-severe",
};

export const bandClasses = (band: Band) => BAND_CLASSES[band];

export function BandBadge({ band, className }: { band: Band; className?: string }) {
  return (
    <span data-band={bandToken(band)}
      className={cn("inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold", BAND_CLASSES[band], className)}>
      {BAND_LABELS[band]}
    </span>
  );
}

// Where a piece of information comes from: measured, modelled, rules, or AI wording.
const SOURCES = {
  measured: { label: "Measured", icon: Gauge, className: "border-success/30 bg-success-soft text-success" },
  forecast: { label: "Forecast", icon: TrendingUp, className: "border-warning/30 bg-warning-soft text-warning" },
  rules: { label: "Rule-based", icon: Cpu, className: "border-border bg-surface-soft text-muted-foreground" },
  ai: { label: "AI-worded", icon: Sparkles, className: "border-ai-border bg-ai-tint text-ai" },
} as const;

export function SourceBadge({ source }: { source: keyof typeof SOURCES }) {
  const { label, icon: Icon, className } = SOURCES[source];
  return (
    <span className={cn("inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium", className)}>
      <Icon className="size-3.5" aria-hidden="true" />
      {label}
    </span>
  );
}
