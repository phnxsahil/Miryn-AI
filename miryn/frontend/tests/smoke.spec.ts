import { test, expect } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";
const API = "http://localhost:8000";

// ─── Backend Smoke Tests ──────────────────────────────────────────────────────

test("backend health returns 200 and db ok", async ({ request }) => {
  const res = await request.get(`${API}/health`);
  expect(res.status()).toBe(200);
  const body = await res.json();
  expect(body.status).toBe("healthy");
  expect(body.checks.db).toBe("ok");
});

test("backend /auth/me requires auth", async ({ request }) => {
  const res = await request.get(`${API}/auth/me`);
  expect(res.status()).toBe(403);
});

test("backend /chat/conversations requires auth", async ({ request }) => {
  const res = await request.get(`${API}/chat/conversations`);
  expect(res.status()).toBe(403);
});

// ─── Landing Page Smoke Tests ─────────────────────────────────────────────────

test("landing page loads and hero visible", async ({ page }) => {
  await page.goto(BASE, { waitUntil: "domcontentloaded" });

  // Title
  await expect(page).toHaveTitle(/Miryn AI/i);

  // Hero communicates the memory-first product promise.
  const hero = page.locator("h1");
  await expect(hero).toBeVisible();
  await expect(hero).toContainText("What can I help with today?");
  await expect(page.getByText("A private thinking companion that remembers the thread.", { exact: true })).toBeVisible();
});

test("landing page keeps the product story and sections discoverable", async ({ page }) => {
  await page.goto(BASE, { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Most chats answer the moment. Miryn keeps the thread." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Start anywhere. Pick up where you left off." })).toBeVisible();
  await expect(page.locator("header").getByRole("link", { name: "FAQ" })).toHaveAttribute("href", "/faq");
});

test("landing page nav links work", async ({ page }) => {
  await page.goto(BASE, { waitUntil: "networkidle" });

  await expect(page.locator("header").getByRole("link", { name: "FAQ" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Try Miryn free" })).toHaveAttribute("href", "/signup");
});

test("landing page primary CTA exists", async ({ page }) => {
  await page.goto(BASE, { waitUntil: "networkidle" });
  const cta = page.locator("a", { hasText: /Start talking|Start free|Try Miryn/i }).first();
  await expect(cta).toBeVisible();
});

test("interactive demo section appears on scroll", async ({ page }) => {
  await page.goto(BASE, { waitUntil: "networkidle" });
  const demo = page.locator("#demo");
  await demo.scrollIntoViewIfNeeded();
  await expect(demo).toBeVisible();
});

test("how it works section has the product comparison", async ({ page }) => {
  await page.goto(BASE, { waitUntil: "networkidle" });
  const section = page.locator("#why");
  await section.scrollIntoViewIfNeeded();
  await expect(section).toContainText("Most chats answer the moment.");
  await expect(section).toContainText("brings it back when it is useful");
});

// ─── Auth Page Smoke Tests ────────────────────────────────────────────────────

test("login page loads", async ({ page }) => {
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
  expect(page.url()).toContain("/login");
  // Should have an email input or Google OAuth button
  const emailOrGoogle = page.locator("input[type='email'], button").first();
  await expect(emailOrGoogle).toBeVisible();
});

test("signup page loads", async ({ page }) => {
  await page.goto(`${BASE}/signup`, { waitUntil: "networkidle" });
  const form = page.locator("form, input").first();
  await expect(form).toBeVisible();
});

test.describe("auth screens", () => {
  test("login form is labeled, mobile-safe, and announces failures", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 740 });
    await page.route("**/auth/refresh", (route) => route.fulfill({ status: 401, body: "{}" }));
    let loginRequestSeen = false;
    await page.route(/\/auth\/login(?:\?.*)?$/, (route) => {
      loginRequestSeen = true;
      return route.fulfill({ status: 401, json: { detail: "Invalid credentials" } });
    });
    await page.goto(`${BASE}/login`);

    await expect(page.getByLabel("Email", { exact: true })).toHaveAttribute("autocomplete", "email");
    await expect(page.getByLabel("Password", { exact: true })).toHaveAttribute("autocomplete", "current-password");
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
    await expect(page.locator("aside")).toBeHidden();
    const authLayout = await page.locator("body").evaluate((element) => {
      const form = element.querySelector("section main")?.getBoundingClientRect();
      const background = getComputedStyle(element).backgroundColor;
      return { background, formWidth: form?.width ?? 0 };
    });
    expect(authLayout.background).toBe("rgb(35, 35, 33)");
    expect(authLayout.formWidth).toBeLessThanOrEqual(400);
    await page.getByLabel("Email", { exact: true }).fill("person@example.com");
    await page.getByLabel("Password", { exact: true }).fill("incorrect-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await expect.poll(() => loginRequestSeen).toBe(true);
    await expect(page.locator(".miryn-error")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  });

  test("signup password reveal is keyboard-operable and meets mobile sizing", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 740 });
    await page.route("**/auth/refresh", (route) => route.fulfill({ status: 401, body: "{}" }));
    await page.goto(`${BASE}/signup`);
    const password = page.getByLabel("Password", { exact: true });
    await expect(password).toHaveAttribute("autocomplete", "new-password");
    await expect(password).toHaveAttribute("minlength", "8");
    await expect(password).toHaveCSS("font-size", "16px");
    const reveal = page.getByRole("button", { name: "Show password" });
    await reveal.focus();
    await expect(reveal).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("button", { name: "Hide password" })).toHaveAttribute("aria-pressed", "true");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  });

  test("password recovery and verification keep one clear primary action", async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 740 });
    await page.route("**/auth/refresh", (route) => route.fulfill({ status: 401, body: "{}" }));
    await page.goto(`${BASE}/forgot-password`);
    await expect(page.getByLabel("Email address")).toHaveAttribute("autocomplete", "email");
    await expect(page.getByRole("button", { name: "Send reset link" })).toBeVisible();
    await expect(page.locator("script[src*='accounts.google.com']")).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);

    await page.goto(`${BASE}/reset-password`);
    await expect(page.locator(".miryn-error")).toContainText("incomplete or invalid");
    await expect(page.getByRole("link", { name: /Request a new reset link/ })).toBeVisible();

    await page.goto(`${BASE}/reset-password?token=preview-token`);
    await expect(page.getByLabel("New password")).toBeVisible();
    await expect(page.getByLabel("Confirm password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Reset password" })).toBeVisible();

    await page.goto(`${BASE}/verify-pending`);
    await expect(page.getByRole("heading", { name: "Check your inbox" })).toBeVisible();
    await expect(page.getByText("No email has been sent from this page.")).toBeVisible();
    await expect(page.getByRole("link", { name: "Return to sign in" })).toBeVisible();
    await expect(page.getByRole("button", { name: /resend|gmail|outlook/i })).toHaveCount(0);
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  });
});
