import { describe, expect, it } from "vitest";
import type { DecisionOut } from "@/lib/api/types";
import { activityLine, decisionHeadline } from "@/lib/labels";

const decision = (changes: Partial<DecisionOut>): DecisionOut => ({
  activity: { kind: "play", start: "17:00:00", duration_min: 60, intensity: "moderate" },
  action: "keep", band_now: "moderate", new_start: null, new_duration_min: null, mask: "none",
  exposure_cut_pct: null, reasons: [], why: "", impact: null, ...changes,
});

describe("plan words", () => {
  it("says each decision in a few words, with a tone that isn't colour alone", () => {
    expect([
      decisionHeadline(decision({})),
      decisionHeadline(decision({ action: "move", new_start: "2026-11-25T13:00:00+05:30" })),
      decisionHeadline(decision({ action: "shorten", new_duration_min: 30 })),
      decisionHeadline(decision({ action: "indoor" })),
    ]).toEqual([
      { text: "Go ahead as planned", tone: "success" },
      { text: "Move to 1 pm", tone: "warning" },
      { text: "Shorten to 30 min", tone: "warning" },
      { text: "Do it indoors today", tone: "danger" },
    ]);
  });

  it("describes the activity as it was entered", () => {
    expect(activityLine(decision({}).activity)).toBe("Outdoor play at 5 pm, 60 min");
  });
});
