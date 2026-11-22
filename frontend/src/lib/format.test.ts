import { describe, expect, it } from "vitest";
import { bandToken, clock, stamp } from "@/lib/format";

describe("format", () => {
  it("shows times the way they're said in India, from the ISO string's own clock", () => {
    expect(["2026-11-25T00:00:00+05:30", "2026-11-25T06:30:00+05:30", "2026-11-25T12:00:00+05:30",
      "2026-11-25T17:00:00+05:30"].map(clock)).toEqual(["12 am", "6:30 am", "12 pm", "5 pm"]);
  });

  it("stamps a reading with its date and time", () => {
    expect(stamp("2026-11-25T13:00:00+05:30")).toBe("25 Nov, 1 pm");
  });

  it("maps a band to its CSS token", () => {
    expect(bandToken("very_poor")).toBe("very-poor");
  });
});
