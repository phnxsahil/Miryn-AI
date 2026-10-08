import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";

async function mockAuthenticatedApi(page: import("@playwright/test").Page) {
  await page.addInitScript(() => {
    localStorage.setItem("miryn_token", "theme-test-token");
    localStorage.removeItem("miryn_refresh_token");
    if (!localStorage.getItem("theme-test-initialized")) {
      localStorage.removeItem("miryn-theme");
      localStorage.setItem("theme-test-initialized", "true");
    }
  });

  await page.route("**/auth/me**", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      id: "theme-user",
      email: "theme@example.com",
      first_name: "Theme",
      full_name: "Theme User",
      notification_preferences: { checkin_reminders: true, weekly_digest: true, browser_push: false },
      data_retention: "forever",
      encryption_enabled: true,
    }),
  }));
  await page.route("**/auth/sessions**", (route) => route.fulfill({ status: 200, contentType: "application/json", body: "[]" }));
  await page.route("**/auth/refresh**", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ access_token: "theme-test-token", refresh_token: "theme-refresh-token" }) }));
  await page.route("**/chat/conversations", (route) => route.fulfill({ status: 200, contentType: "application/json", body: "[]" }));
  await page.route("**/memory/", (route) => route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ recent: [], facts: [], emotions: [] }) }));
  await page.route("**/identity/", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ id: "identity-1", email: "theme@example.com", state: "forming", traits: {}, values: {}, beliefs: [], open_loops: [], patterns: [], conflicts: [] }),
  }));
  await page.route("**/identity/evolution", (route) => route.fulfill({ status: 200, contentType: "application/json", body: "[]" }));
  await page.route("**/onboarding/presets", (route) => route.fulfill({ status: 200, contentType: "application/json", body: "[]" }));
}

test("Settings theme toggle propagates across authenticated routes without refresh", async ({ page }) => {
  test.setTimeout(60000);
  await mockAuthenticatedApi(page);
  let reloads = 0;
  page.on("framenavigated", (frame) => {
    if (frame === page.mainFrame()) reloads += 1;
  });

  await page.goto(`${BASE}/settings`, { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("button", { name: "Switch to light theme" })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  reloads = 0;

  await page.getByRole("button", { name: "Switch to light theme" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("button", { name: "Switch to dark theme" })).toHaveText("Light theme");
  expect(reloads).toBe(0);
  await expect.poll(() => page.evaluate(() => localStorage.getItem("miryn-theme"))).toBe("light");

  const routes = [
    { path: "/chat", assert: () => expect(page.getByLabel("Message Miryn")).toBeVisible() },
    { path: "/memory", assert: () => expect(page.getByText("Your memory is empty", { exact: true })).toBeVisible() },
    { path: "/identity", assert: () => expect(page.locator("main").or(page.locator("body"))).toBeVisible() },
    { path: "/onboarding", assert: () => expect(page.getByText(/What should Miryn|How should Miryn show up|Step \d of 4/).first()).toBeVisible() },
  ];

  for (const route of routes) {
    await page.goto(`${BASE}${route.path}`, { waitUntil: "domcontentloaded" });
    await route.assert();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    const background = await page.locator("body").evaluate((element) => getComputedStyle(element).backgroundColor);
    expect(background).toBe("rgb(250, 248, 242)");
  }

  await page.goto(`${BASE}/settings`, { waitUntil: "domcontentloaded" });
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});
