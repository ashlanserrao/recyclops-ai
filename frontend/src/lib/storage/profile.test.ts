import { beforeEach, describe, expect, it, vi } from "vitest";
import { DEMOS } from "@/lib/demo-households";
import { loadProfile, PROFILE_KEY, saveProfile } from "@/lib/storage/profile";

describe("saved profile", () => {
  beforeEach(() => {
    const items = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => items.get(key) ?? null,
      setItem: (key: string, value: string) => items.set(key, value),
      removeItem: (key: string) => items.delete(key),
    });
  });

  it("comes back as it was saved", () => {
    const profile = DEMOS[0]!.profile;
    saveProfile(profile);
    expect(loadProfile()).toEqual(profile);
  });

  it("is ignored when it can't be read", () => {
    for (const raw of ["{not json", JSON.stringify({ place: { source: "city" }, household: { members: [] } })]) {
      localStorage.setItem(PROFILE_KEY, raw);
      expect(loadProfile()).toBeNull();
    }
  });

  it("is null when storage is blocked", () => {
    vi.stubGlobal("localStorage", { getItem: () => { throw new Error("blocked"); } });
    expect(loadProfile()).toBeNull();
  });
});
