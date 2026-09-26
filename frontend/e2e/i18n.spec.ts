// V1.3 i18n E2E: locale switching, persistence, no console errors.
// Real browser against the live dev stack. No API interception.
import { test, expect, type Page } from "@playwright/test";

test.use({ baseURL: "http://127.0.0.1:3000" });

// Markets re-renders while data loads, which can detach the select node
// between Playwright's check and dispatch. Re-issue the user action
// until it sticks (a real user simply clicks the live control).
async function selectLocale(page: Page, code: string) {
  await expect
    .poll(
      async () => {
        await page
          .locator("header select")
          .first()
          .selectOption(code)
          .catch(() => {});
        await page.waitForTimeout(400);
        return page.locator("html").getAttribute("lang");
      },
      { timeout: 20000 }
    )
    .toBe(code);
}

test("locale switch to Telugu localizes shell and persists", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/markets");
  await expect(page.getByRole("link", { name: "Markets" })).toBeVisible();

  // Switch via the header language selector (sidebar has its own copy).
  await selectLocale(page, "te");
  await expect(page.getByRole("link", { name: "మార్కెట్లు" })).toBeVisible();

  // Reload: locale + selection survive.
  await page.reload();
  await expect(page.getByRole("link", { name: "మార్కెట్లు" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("assistant page renders in Hindi after switch", async ({ page }) => {
  await page.goto("/ai-assistant");
  await selectLocale(page, "hi");
  // Assistant shell heading uses the Hindi catalog.
  await expect(page.getByText("AI सहायक").first()).toBeVisible();
});

test("urdu sets rtl document direction and persists", async ({ page }) => {
  await page.goto("/markets");
  await selectLocale(page, "ur");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.locator("html")).toHaveAttribute("lang", "ur");
});
