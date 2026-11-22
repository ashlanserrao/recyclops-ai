import { describe, expect, it } from "vitest";
import { DEMOS } from "@/lib/demo-households";
import { devicePlace, errorMap, missingFields, newHousehold, newMember } from "@/lib/household";

describe("household setup", () => {
  it("gives each new member an id no one else has", () => {
    const first = newMember([]);
    const second = newMember([{ ...first, id: "m2" }]);
    expect([first.id, second.id]).toEqual(["m1", "m3"]);
  });

  it("names every blank entry by the server's field path", () => {
    const household = newHousehold();
    household.members[0]!.activities = [{ kind: "walk", start: "", duration_min: Number.NaN, intensity: "light" }];
    expect(missingFields({ place: null, household }).map((error) => error.field)).toEqual([
      "location",
      "household.members.0.name",
      "household.members.0.age",
      "household.members.0.activities.0.start",
      "household.members.0.activities.0.duration_min",
    ]);
  });

  it("finds nothing missing in the demo households", () => {
    for (const demo of DEMOS) expect(missingFields(demo.profile)).toEqual([]);
  });

  it("keeps the first message when a field has two", () => {
    expect(errorMap([{ field: "a", message: "first" }, { field: "a", message: "second" }])).toEqual({ a: "first" });
  });

  it("rounds a device position to about a kilometre, and only inside India", () => {
    expect(devicePlace(28.61394, 77.20902)).toEqual({ source: "device", name: null, lat: 28.61, lon: 77.21 });
    expect(devicePlace(51.5, -0.12)).toBeNull();
  });
});
