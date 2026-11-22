import { expect, test } from "@playwright/test";

test("the built site loads with its landmarks", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "Plan your household's day around the air" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeAttached();
  await expect(page.getByRole("group", { name: "Colour theme" })).toBeVisible();
});
