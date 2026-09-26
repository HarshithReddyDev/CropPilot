/**
 * Phase 8 E2E: assistant chat flows (§44).
 *
 * Requires the full stack: backend on :8000, frontend on :3000,
 * NEXT_PUBLIC_DEV_AUTH_BYPASS=true. Not runnable in this sandbox
 * (no browsers, docker down). CI: `npx playwright test e2e/assistant.spec.ts`.
 */
import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.goto("/ai-assistant");
});

test("chat flow renders assistant reply", async ({ page }) => {
  await page.getByPlaceholder(/ask/i).fill("What is the wheat price in Telangana?");
  await page.getByRole("button", { name: /send/i }).click();
  await expect(page.getByText(/quintal|wheat|telangana/i).last()).toBeVisible({
    timeout: 60_000,
  });
});

test("apply-market-filters action deep-links to markets page", async ({ page }) => {
  await page.getByPlaceholder(/ask/i).fill("Show wheat prices in Telangana");
  await page.getByRole("button", { name: /send/i }).click();
  await page.waitForURL(/\/markets\?/, { timeout: 60_000 });
  expect(page.url()).toContain("commodity=");
});

test("backend outage shows error banner, not a hang", async ({ page }) => {
  await page.route("**/api/v1/assistant/**", (route) => route.abort());
  await page.getByPlaceholder(/ask/i).fill("Hello");
  await page.getByRole("button", { name: /send/i }).click();
  await expect(page.getByText(/couldn.*t reach|try again|unavailable/i).first()).toBeVisible({
    timeout: 30_000,
  });
});
