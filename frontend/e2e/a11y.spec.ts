// Automated WCAG 2.1 A/AA scan (axe) of every screen state: setup, its errors, the plan in both themes, and Ask.

import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";
import { DELHI_ASK, serveAsk, servePlan } from "./stubs";

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

async function expectNoViolations(page: Page) {
  const { violations } = await new AxeBuilder({ page }).withTags(WCAG).analyze();
  const summary = violations.map((v) => `${v.id}: ${v.help} (${v.nodes.map((n) => n.target.join(" ")).join(", ")})`);
  expect(summary).toEqual([]);
}

test("the setup form, empty and with errors", async ({ page }) => {
  await page.goto("/");
  await expectNoViolations(page);
  await page.getByRole("button", { name: "Save household" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expectNoViolations(page);
});

for (const scheme of ["light", "dark"] as const) {
  test(`the plan and an Ask answer, ${scheme} theme`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: scheme });
    await servePlan(page);
    await serveAsk(page);
    await page.goto("/");
    await page.getByRole("button", { name: /Delhi family/ }).click();
    await expect(page.getByRole("region", { name: "Air in Delhi" })).toBeVisible();
    await expectNoViolations(page);

    const ask = page.getByRole("region", { name: "Can we…?" });
    await ask.getByRole("button", { name: "Use the example" }).click();
    await ask.getByRole("button", { name: "Ask" }).click();
    await expect(ask.getByText("Read by AI")).toBeVisible();
    await expectNoViolations(page);
  });
}

test("the Ask form fallback", async ({ page }) => {
  await servePlan(page);
  await serveAsk(page, DELHI_ASK.needs_form);
  await page.goto("/");
  await page.getByRole("button", { name: /Delhi family/ }).click();
  const ask = page.getByRole("region", { name: "Can we…?" });
  await ask.getByLabel("Your question").fill("Can Aarav play cricket at 6 pm?");
  await ask.getByRole("button", { name: "Ask" }).click();
  await expect(ask.getByLabel("Who")).toBeFocused();
  await expectNoViolations(page);
});
