import { expect, test } from "@playwright/test";

test("an example household saves in one click and is still there after a reload", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /Delhi family/ }).click();

  const household = page.getByRole("region", { name: "Your household" });
  await expect(household).toContainText("Delhi · Aarav (8), Dadi (68), Priya (38)");
  await expect(page.getByRole("button", { name: "Edit household" })).toBeFocused();

  await page.reload();
  await expect(household).toContainText("Delhi · Aarav (8), Dadi (68), Priya (38)");
});

test("your own household: blank entries are named, then it saves", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Save household" }).click();

  await expect(page.getByRole("alert")).toContainText("3 entries need a look.");
  const city = page.getByLabel("City");
  await expect(city).toBeFocused();
  await expect(city).toHaveAccessibleDescription("Choose a city or use your location.");

  await city.selectOption("Kolkata");  // the list comes from the backend's /api/cities
  await page.getByLabel("Name or nickname").fill("Rohan");
  await page.getByLabel("Age").fill("19");
  await page.getByLabel("Regular commute").selectOption("bus");
  await page.getByRole("button", { name: "Save household" }).click();

  await expect(page.getByRole("region", { name: "Your household" })).toContainText("Kolkata · Rohan (19)");
});
