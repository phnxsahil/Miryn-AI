import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";

test("conversation sidebar exposes menu actions and protects delete", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("miryn_token", "conversation-test-token"));
  await page.route("**/auth/me**", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ id: "u", email: "u@example.com", first_name: "Test", full_name: "Test", notification_preferences: {}, data_retention: "forever", encryption_enabled: true }),
  }));
  await page.route("**/chat/conversations**", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify([
      { id: "active-chat", title: "Active thread", is_pinned: false, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), message_count: 2 },
      { id: "pinned-chat", title: "Pinned thread", is_pinned: true, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), message_count: 1 },
    ]),
  }));
  await page.route("**/chat/conversations/*/pin", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "success", pinned: true }) }));
  await page.route("**/chat/conversations/*/title", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "success", title: "Renamed thread" }) }));
  await page.route("**/chat/conversations/*", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "success" }) }));
  await page.route("**/chat/history**", (route) => route.fulfill({ status: 200, contentType: "application/json", body: "[]" }));

  await page.goto(`${BASE}/chat?id=active-chat`, { waitUntil: "domcontentloaded" });
  const active = page.locator("a[href='/chat?id=active-chat']");
  await expect(active).toBeVisible();
  await active.hover();
  const menuButton = page.getByRole("button", { name: "More options for Active thread" }).first();
  await expect(menuButton).toBeVisible();
  await menuButton.click();
  await expect(page.getByRole("button", { name: "Rename" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Pin", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Delete" })).toBeVisible();

  await page.getByRole("button", { name: "Pin", exact: true }).click();
  await expect(page.getByText("Pinned", { exact: true })).toBeVisible();

  await menuButton.hover();
  await menuButton.click();
  await page.getByRole("button", { name: "Delete" }).click();
  await expect(page.getByRole("dialog")).toContainText("Delete conversation?");
  await expect(page.getByRole("dialog").getByRole("button", { name: "Cancel" })).toBeVisible();
  await page.getByRole("dialog").getByRole("button", { name: "Cancel" }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});
