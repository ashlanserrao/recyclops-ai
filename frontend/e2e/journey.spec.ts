// The spec's end-to-end proof: example household -> AQI -> a person's advice -> a question -> reload -> keyboard.

import { expect, test } from "@playwright/test";
import { DELHI_ASK, serveAsk, servePlan } from "./stubs";

test("the main journey, start to finish", async ({ page }) => {
  await servePlan(page);
  await serveAsk(page);
  await page.goto("/");
  await page.getByRole("button", { name: /Delhi family/ }).click();

  await expect(page.getByRole("region", { name: "Air in Delhi" })).toContainText("AQI354Very poor");
  await expect(page.getByRole("region", { name: "Each person's day" }).getByRole("listitem").filter({ hasText: "Aarav" }))
    .toContainText("Move to 1 pm");

  const ask = page.getByRole("region", { name: "Can we…?" });
  await ask.getByLabel("Your question").fill("Can Aarav play cricket at 6 pm?");
  await ask.getByRole("button", { name: "Ask" }).click();
  await expect(ask).toContainText("Better at another time");
  await expect(ask).toContainText("Understood as: Aarav, sport at 6 pm, 60 min, Wed, 25 Nov");
  await expect(ask.getByText("Read by AI")).toBeVisible();
  await expect(ask).toContainText("1 pm to 1:30 pm, 30 minutes: about 77% less PM2.5 breathed in.");

  await page.reload();
  await expect(page.getByRole("region", { name: "Your household" })).toContainText("Delhi · Aarav (8), Dadi (68), Priya (38)");

  // Every stop on the Tab path, from the top of the freshly loaded page, is on screen and shows a focus ring.
  const seen = new Set<string>();
  for (let stop = 0; stop < 40; stop += 1) {
    await page.keyboard.press("Tab");
    const focused = await page.evaluate(() => {
      const element = document.activeElement as HTMLElement | null;
      if (!element || element === document.body) return null;
      const style = getComputedStyle(element);
      const position = Array.from(document.querySelectorAll("*")).indexOf(element);
      const label = element.getAttribute("aria-label")
        ?? (element instanceof HTMLInputElement ? element.labels?.[0]?.textContent : element.textContent);
      return { name: `${position} ${label?.trim()}`,
        ring: style.outlineStyle !== "none" || style.boxShadow !== "none" };
    });
    if (!focused || seen.has(focused.name)) break;
    seen.add(focused.name);
    expect(focused.ring, `focus ring on ${focused.name}`).toBe(true);
    await expect(page.locator(":focus")).toBeInViewport();
  }
  expect([...seen].map((name) => name.replace(/^\d+ /, ""))).toEqual([
    "Skip to content", "Light", "Dark", "Match device", "Edit household", "Refresh",
    "Your question", "Ask", "Use the example", "Use the form instead",
  ]);
});

test("when the question can't be read, the form answers it instead", async ({ page }) => {
  await servePlan(page);
  await serveAsk(page, DELHI_ASK.needs_form);
  await page.goto("/");
  await page.getByRole("button", { name: /Delhi family/ }).click();

  const ask = page.getByRole("region", { name: "Can we…?" });
  await ask.getByLabel("Your question").fill("Can Aarav play cricket at 6 pm?");
  await ask.getByRole("button", { name: "Ask" }).click();
  await expect(ask).toContainText("needs the AI, which isn't available right now");
  await expect(ask.getByLabel("Who")).toBeFocused();

  await ask.getByLabel("Activity").selectOption("sport");
  await ask.getByLabel("Starts at").fill("18:00");
  await ask.getByLabel("Effort").selectOption("high");
  await ask.getByRole("button", { name: "Check" }).click();
  await expect(ask).toContainText("Better at another time");
  await expect(ask.getByText("Read by AI")).toHaveCount(0);
});
