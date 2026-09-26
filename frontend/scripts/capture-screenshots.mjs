import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDir, "../..");
const outputRoot = path.join(repoRoot, "docs", "screenshots");
const baseUrl = (process.env.CROPPILOT_URL || "http://127.0.0.1:3000").replace(/\/$/, "");
const failures = [];

const desktop = [
  ["01-home.png", "/"],
  ["03-markets.png", "/markets"],
  ["05-disease-detection.png", "/disease-detection"],
  ["06-schemes.png", "/schemes"],
  ["08-maps.png", "/maps?lat=17.05&lng=79.27&zoom=8"],
  ["09-ai-assistant.png", "/ai-assistant"],
  ["10-login.png", "/auth/login"],
];

const mobile = [
  ["02-markets.png", "/markets"],
  ["04-disease-detection.png", "/disease-detection"],
  ["05-maps.png", "/maps?lat=17.05&lng=79.27&zoom=8"],
  ["06-ai-assistant.png", "/ai-assistant"],
];

const localized = [
  ["hi-markets.png", "/markets", "hi"],
];

async function capture(browser, directory, filename, route, options = {}) {
  const page = await browser.newPage({
    viewport: options.viewport || { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    isMobile: Boolean(options.mobile),
    hasTouch: Boolean(options.mobile),
    colorScheme: "dark",
  });
  const pageErrors = [];
  page.on("pageerror", (error) => pageErrors.push(String(error)));
  try {
    await page.goto(`${baseUrl}${route}`, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    if (options.locale) {
      const selector = page.getByRole("combobox", { name: /select language/i }).first();
      if (await selector.count()) await selector.selectOption(options.locale);
      await page.waitForTimeout(800);
    }
    await page.waitForTimeout(1200);
    const bodyText = await page.locator("body").innerText().catch(() => "");
    if (/Demo Mode|sample data/i.test(bodyText)) {
      console.log(`SKIP ${filename}: UI explicitly reports demo/sample data`);
      return false;
    }
    // Known mock-data pages: dashboard/analytics render MOCK_DASHBOARD_DATA
    // and hardcoded chart series; weather renders Math.random forecasts.
    // Never publish these routes as release evidence.
    if (/^\/(dashboard|analytics|weather)/.test(route)) {
      console.log(`SKIP ${filename}: route renders known mock data, not release evidence`);
      return false;
    }
    if (pageErrors.length) {
      console.log(`SKIP ${filename}: browser error (${pageErrors[0]})`);
      failures.push(`${filename}: ${pageErrors[0]}`);
      return false;
    }
    await fs.mkdir(directory, { recursive: true });
    await page.screenshot({ path: path.join(directory, filename), animations: "disabled" });
    console.log(`CAPTURED ${path.relative(repoRoot, path.join(directory, filename))}`);
    return true;
  } catch (error) {
    console.log(`SKIP ${filename}: ${String(error)}`);
    failures.push(`${filename}: ${String(error)}`);
    return false;
  } finally {
    await page.close();
  }
}

await fs.mkdir(outputRoot, { recursive: true });
const browser = await chromium.launch({ headless: true });
try {
  for (const [name, route] of desktop) {
    await capture(browser, path.join(outputRoot, "desktop"), name, route);
  }
  for (const [name, route] of mobile) {
    await capture(browser, path.join(outputRoot, "mobile"), name, route, {
      mobile: true,
      viewport: { width: 390, height: 844 },
    });
  }
  for (const [name, route, locale] of localized) {
    await capture(browser, path.join(outputRoot, "localized"), name, route, { locale });
  }
} finally {
  await browser.close();
}

if (failures.length) {
  console.log(`Skipped ${failures.length} capture(s); see reasons above.`);
}
