import { expect, test } from "@playwright/test";

test("navigates from live games to a game detail page", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Live Games" }),
  ).toBeVisible();

  const gameLinks = page.locator('a[href^="/games/"]');
  await expect(gameLinks.first()).toBeVisible();

  await gameLinks.first().click();

  await expect(page).toHaveURL(/\/games\/[^/]+$/);
  await expect(page.getByText("Player Stats")).toBeVisible();
  await expect(page.getByText("Team Stats")).toBeVisible();
});
