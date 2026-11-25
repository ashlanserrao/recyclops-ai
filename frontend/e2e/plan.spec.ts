import { expect, test } from "@playwright/test";
import { DELHI_PLAN, servePlan } from "./stubs";

test("the Delhi example shows the measured AQI and each person's advice", async ({ page }) => {
  await servePlan(page, DELHI_PLAN);
  await page.goto("/");
  await page.getByRole("button", { name: /Delhi family/ }).click();

  await expect(page.getByRole("status")).toHaveText("Plan ready for Delhi. AQI 354, Very poor.");
  const air = page.getByRole("region", { name: "Air in Delhi" });
  await expect(air).toContainText("AQI354Very poorMostly PM2.5");
  await expect(air).toContainText("ITO, Delhi - CPCB, 2.3 km away");
  await expect(air).toContainText("25 Nov, 12 pm");
  await expect(air).toContainText("Cleanest 2 hours1 pm to 3 pm");

  const people = page.getByRole("region", { name: "Each person's day" });
  const aarav = people.getByRole("listitem").filter({ hasText: "Aarav" });
  await expect(aarav).toContainText("Move to 1 pm");
  await expect(aarav).toContainText("about 77% less PM2.5 breathed in");
  await expect(people.getByRole("listitem").filter({ hasText: "Dadi" })).toContainText("Do it indoors today");
  await expect(page.getByRole("region", { name: "Getting around" })).toContainText("Take the metroSaves about 19.8 kg");
  await expect(page.getByText("AI-worded")).toHaveCount(0);  // template wording carries no AI label
});

test("AI-worded explanations are labelled as such", async ({ page }) => {
  await servePlan(page, { ...DELHI_PLAN, ai_used: true });
  await page.goto("/");
  await page.getByRole("button", { name: /Delhi family/ }).click();
  await expect(page.getByRole("region", { name: "Each person's day" }).getByText("AI-worded").first()).toBeVisible();
});

test("without live air data the app says so and offers a retry", async ({ page }) => {
  await page.goto("/");  // the real backend: no air-data key in tests
  await page.getByRole("button", { name: /Mumbai senior/ }).click();
  await expect(page.getByRole("alert")).toContainText("Live air-quality data isn't available right now.");
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Your household" })).toContainText("Mumbai · Nana (70)");
});

test("a value the server rejects reopens the form on that field", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("City").selectOption("Pune");
  await page.getByLabel("Name or nickname").fill("Ajoba");
  await page.getByLabel("Age").fill("150");
  await page.getByRole("button", { name: "Save household" }).click();

  const age = page.getByLabel("Age");
  await expect(age).toBeFocused();
  await expect(age).toHaveAccessibleDescription("Input should be less than or equal to 110");
});
