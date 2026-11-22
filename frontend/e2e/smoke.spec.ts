import { expect, test } from "@playwright/test";

test("the built site loads and reaches the API", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1, name: "recyclops-ai" })).toBeVisible();
  await expect(page.getByText("Service status: ok")).toBeVisible();
});
