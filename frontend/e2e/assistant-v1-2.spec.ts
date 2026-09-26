/**
 * V1.2 E2E: assistant core/security/failure flows (§7-9) against the REAL stack.
 *
 * Requires: backend :8000, frontend 127.0.0.1:3000, NEXT_PUBLIC_DEV_AUTH_BYPASS=true,
 * Ollama warm (cold first turn can take ~75s on CPU).
 * Run: `npx playwright test e2e/assistant-v1-2.spec.ts --workers=1`
 */
import { test, expect } from "@playwright/test";

test.use({ baseURL: "http://127.0.0.1:3000" });

const ask = (page: import("@playwright/test").Page, text: string) =>
  page.getByPlaceholder(/ask/i).fill(text);

const send = (page: import("@playwright/test").Page) =>
  page.getByPlaceholder(/ask/i).press("Enter");

test.describe("core flows", () => {
  test("TEST 1 dashboard loads", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/croppilot/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test("TEST 2 ai-assistant page loads", async ({ page }) => {
    await page.goto("/ai-assistant");
    await expect(page.getByPlaceholder(/ask/i)).toBeVisible({ timeout: 30_000 });
  });

  test("TEST 3 hello gets real backend reply", async ({ page }) => {
    test.setTimeout(180_000);
    await page.goto("/ai-assistant");
    await ask(page, "Hello");
    const [resp] = await Promise.all([
      page.waitForResponse(/\/api\/v1\/assistant\/chat\/stream/, { timeout: 150_000 }),
      send(page),
    ]);
    expect(resp.ok()).toBeTruthy();
    // Scope to the last bubble: the user echo ("Hello") must not satisfy this.
    await expect(page.locator("main div.group").last().getByText(/namaste|how can|help you|farmer/i)).toBeVisible({
      timeout: 150_000,
    });
  });

  test("TEST 4 tomato Nalgonda returns real market data", async ({ page }) => {
    test.setTimeout(300_000);
    await page.goto("/ai-assistant");
    await ask(page, "Show tomato prices in Nalgonda.");
    await send(page);
    // quintal/price figures come only from the market tool, never the echo.
    await expect(page.locator("main div.group").last().getByText(/quintal|per kg|modal price/i)).toBeVisible({
      timeout: 240_000,
    });
  });

  test("TEST 5 semantic action deep-links to markets", async ({ page }) => {
    test.setTimeout(300_000);
    await page.goto("/ai-assistant");
    await ask(page, "Show wheat prices in Telangana");
    await send(page);
    await page.waitForURL(/\/markets\?/, { timeout: 240_000 });
    expect(page.url()).toContain("commodity=");
  });

  test("TEST 6 markets page still works after action nav", async ({ page }) => {
    test.setTimeout(180_000);
    await page.goto("/markets?commodity=Wheat&state=Telangana");
    await expect(page.getByText(/wheat/i).first()).toBeVisible({ timeout: 60_000 });
  });

  test("TEST 7 weather question answered or clarified, never fabricated-market", async ({
    page,
  }) => {
    test.setTimeout(300_000);
    await page.goto("/ai-assistant");
    await ask(page, "What is the weather like for my farm?");
    await send(page);
    // Scope to the reply: the user echo already contains "weather".
    await expect(page.locator("main div.group").last().getByText(/temperature|rain|humidity|forecast|which location|h3 index/i)).toBeVisible({
      timeout: 240_000,
    });
  });

  test("TEST 8 RAG answer carries citation", async ({ page }) => {
    test.setTimeout(300_000);
    await page.goto("/ai-assistant");
    await ask(page, "What is the premium subsidy under PMFBY?");
    await send(page);
    // Citation sources render only on assistant replies, never on echoes.
    await expect(page.getByText(/source/i).last()).toBeVisible({
      timeout: 240_000,
    });
  });

  test("TEST 9 second message keeps history", async ({ page }) => {
    test.setTimeout(300_000);
    await page.goto("/ai-assistant");
    await ask(page, "Hello");
    await send(page);
    // First turn rendered: sidebar + welcome + user + assistant.
    await expect(page.locator("main div.group")).toHaveCount(4, {
      timeout: 150_000,
    });
    await ask(page, "What can you help with?");
    await send(page);
    // Six .group nodes: sidebar entry + welcome + 2 user + 2 assistant turns.
    await expect(page.locator("main div.group")).toHaveCount(6, { timeout: 150_000 });
  });

  test("TEST 10 reload keeps thread history", async ({ page }) => {
    test.setTimeout(300_000);
    await page.goto("/ai-assistant");
    await ask(page, "Hello");
    await send(page);
    await expect(page.locator("main div.group").last().getByText(/namaste|how can|help you|farmer/i)).toBeVisible({
      timeout: 150_000,
    });
    await page.reload();
    // Thread persists across reload: sidebar entry + welcome + user + assistant.
    await expect(page.locator("main div.group")).toHaveCount(4, { timeout: 60_000 });
  });
});

test.describe("security flows", () => {
  test("malicious ui_action from stream is ignored", async ({ page }) => {
    await page.goto("/ai-assistant");
    await page.route("**/api/v1/assistant/chat/stream", async (route) => {
      const sse =
        `event: final\n` +
        `data: ${JSON.stringify({
          text: "Hi",
          ui_actions: [
            { type: "execute.javascript", payload: { code: "alert(1)" } },
            { type: "open-market", payload: { url: "https://example.com" } },
            { type: "unknown.action", payload: {} },
          ],
        })}\n\n`;
      await route.fulfill({
        status: 200,
        headers: { "content-type": "text/event-stream" },
        body: sse,
      });
    });
    await ask(page, "Hello");
    await send(page);
    await page.waitForTimeout(3000);
    expect(page.url()).toContain("/ai-assistant");
  });
});

test.describe("failure flows", () => {
  test("backend outage shows error, no hang", async ({ page }) => {
    await page.route("**/api/v1/assistant/**", (route) => route.abort());
    await page.goto("/ai-assistant");
    await ask(page, "Hello");
    await send(page);
    await expect(page.locator("main div.group").last().getByText(/couldn.*t reach|try again|unavailable|error/i)).toBeVisible({
      timeout: 30_000,
    });
  });
});
