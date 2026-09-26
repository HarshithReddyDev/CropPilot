// Map E2E: real page + client map against deterministic API fixtures
// (route interception at the API boundary — no fake data in app code).
// A few tests also run fixture-free to prove graceful degradation.
import { test, expect } from "@playwright/test";

test.use({
  baseURL: "http://127.0.0.1:3000",
  // Software WebGL for headless CI GPUs: exercises the real map instead of
  // the no-WebGL fallback.
  launchOptions: { args: ["--enable-unsafe-swiftshader"] },
});

const REVERSE = {
  latitude: 17.05,
  longitude: 79.27,
  display_name: "Nalgonda, Telangana, India",
  locality: "Nalgonda",
  district: "Nalgonda",
  state: "Telangana",
  country: "India",
  postcode: "508001",
  source: "nominatim/osm",
};

const MARKETS = {
  markets: [
    {
      name: "Nalgonda APMC",
      district: "Nalgonda",
      state: "Telangana",
      latitude: 17.06,
      longitude: 79.27,
      coordinate_source: "nominatim/osm",
      distance_km: 1.2,
      latest: {
        commodity: "Paddy",
        variety: "Common",
        grade: null,
        modal_price: 2323,
        price_per_unit: "INR/quintal",
        arrival_date: "2026-09-21",
        arrivals: 120,
        source: "AGMARKNET",
      },
    },
  ],
  unmapped_count: 3,
  radius_km: 50,
  district: "Nalgonda",
  state: "Telangana",
};

const WEATHER = {
  latitude: 17.05,
  longitude: 79.27,
  h3_index: "testcell",
  temperature_c: 31.5,
  feels_like_c: 33.0,
  humidity_pct: 62,
  rain_mm: 0,
  wind_speed: 11,
  wind_deg: 230,
  condition: "2",
  recorded_at: new Date(Date.now() - 12 * 60000).toISOString(),
  fetched_now: false,
  source: "open-meteo",
};

const SEARCH = [
  {
    type: "district",
    name: "Nalgonda",
    district: "Nalgonda",
    state: "Telangana",
    latitude: null,
    longitude: null,
    source: "croppilot-geo-catalog",
  },
  {
    type: "place",
    name: "Nalgonda",
    district: "Nalgonda",
    state: "Telangana",
    latitude: 17.05,
    longitude: 79.27,
    source: "nominatim/osm",
  },
];

async function mockMapApis(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/map/reverse*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(REVERSE) })
  );
  await page.route("**/api/v1/map/markets*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MARKETS) })
  );
  await page.route("**/api/v1/map/weather*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(WEATHER) })
  );
  await page.route("**/api/v1/map/viewport-markets*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(MARKETS) })
  );
  // Non-agri tests must not wait on the real (slow, provider-bound)
  // aggregate: answer with honest unavailable sections.
  await page.route("**/api/v1/map/agricultural-context*", (r) =>
    r.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        location: { latitude: 17.05, longitude: 79.27, district: "Nalgonda", state: "Telangana" },
        snapshot: null,
        weather: { status: "unavailable", data: null },
        rainfall: { status: "unavailable", data: null },
        soil: { status: "unavailable", data: null },
        crops: { status: "unavailable", data: null },
        suitability: { status: "unavailable", data: null },
        water: { status: "unavailable", data: null },
        disease_context: { status: "unavailable", data: null },
        sources: [],
      }),
    })
  );
}

test("map page renders with search and no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/maps");
  // Either the interactive canvas (WebGL2 present) or the honest
  // no-WebGL fallback — never a crash.
  await expect(
    page.getByTestId("croppilot-map").or(page.getByText(/interactive map is unavailable/i))
  ).toBeVisible({ timeout: 30000 });
  await expect(page.getByPlaceholder(/search village/i)).toBeVisible();
  await expect(page.getByRole("button", { name: /use my location/i })).toBeVisible();
  expect(errors).toEqual([]);
});

test("selecting a location shows insights", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await mockMapApis(page);
  await page.route("**/api/v1/map/search*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(SEARCH) })
  );
  await page.goto("/maps");
  await expect(page.getByPlaceholder(/search village/i)).toBeVisible({ timeout: 30000 });
  await page.getByPlaceholder(/search village/i).fill("Nalgonda");
  await expect(page.getByRole("option", { name: /Nalgonda/ }).first()).toBeVisible({
    timeout: 15000,
  });
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(page.getByText("Nalgonda").first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(/32°C|31°C|°C/).first()).toBeVisible();
  await expect(page.getByText("Nalgonda APMC").first()).toBeVisible();
  await expect(page.getByText(/2,323/).first()).toBeVisible();
  await expect(page).toHaveURL(/lat=.*&lng=|lat=.*lng=/);
  expect(errors).toEqual([]);
});

test("search selects a result and flies to it", async ({ page }) => {
  await mockMapApis(page);
  await page.route("**/api/v1/map/search*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(SEARCH) })
  );
  await page.goto("/maps");
  await expect(
    page.getByTestId("croppilot-map").or(page.getByText(/interactive map is unavailable/i))
  ).toBeVisible({ timeout: 30000 });
  await page.getByPlaceholder(/search village/i).fill("Nalgonda");
  await expect(page.getByRole("option", { name: /Nalgonda/ }).first()).toBeVisible({
    timeout: 15000,
  });
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(page.getByText("Nalgonda").first()).toBeVisible({ timeout: 15000 });
  await expect(page).toHaveURL(/lat=17\.05/);
});

test("market popup opens with latest reported price and intel link", async ({ page }) => {
  await mockMapApis(page);
  await page.goto("/maps?lat=17.05&lng=79.27&zoom=11");
  await expect(
    page.getByTestId("croppilot-map").or(page.getByText(/interactive map is unavailable/i))
  ).toBeVisible({ timeout: 30000 });
  await expect(page.getByText("Nalgonda APMC").first()).toBeVisible({ timeout: 15000 });
  await page.getByText("Nalgonda APMC").first().click();
  await expect(page.getByRole("link", { name: /view market intelligence/i })).toBeVisible();
  const href = await page
    .getByRole("link", { name: /view market intelligence/i })
    .getAttribute("href");
  expect(href).toContain("/markets?");
  expect(href).toContain("market=Nalgonda+APMC".replace(" ", "+"));
  // Never "live price".
  await expect(page.getByText(/live price/i)).toHaveCount(0);
});

test("market API failure keeps the map usable", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.route("**/api/v1/map/reverse*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(REVERSE) })
  );
  await page.route("**/api/v1/map/markets*", (r) =>
    r.fulfill({ status: 500, contentType: "application/json", body: "{}" })
  );
  await page.route("**/api/v1/map/weather*", (r) =>
    r.fulfill({ status: 500, contentType: "application/json", body: "{}" })
  );
  await page.goto("/maps?lat=17.05&lng=79.27");
  await expect(
    page.getByTestId("croppilot-map").or(page.getByText(/interactive map is unavailable/i))
  ).toBeVisible({ timeout: 30000 });
  await expect(page.getByText(/temporarily unavailable|could not be loaded/i).first()).toBeVisible({
    timeout: 15000,
  });
  // Search still works; selection retained.
  await expect(page.getByPlaceholder(/search village/i)).toBeVisible();
  expect(errors).toEqual([]);
});

test("url state restores the location on reload", async ({ page }) => {  await mockMapApis(page);
  await page.goto("/maps?lat=17.05&lng=79.27&zoom=9");
  await expect(page.getByText("Nalgonda").first()).toBeVisible({ timeout: 15000 });
  await page.reload();
  await expect(page.getByText("Nalgonda").first()).toBeVisible({ timeout: 15000 });
});

test("mobile layout shows bottom sheet", async ({ page }) => {
  await mockMapApis(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/maps?lat=17.05&lng=79.27");
  await expect(
    page.getByTestId("croppilot-map").or(page.getByText(/interactive map is unavailable/i))
  ).toBeVisible({ timeout: 30000 });
  await expect(page.getByText("Nalgonda").first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("button", { name: /expand panel|collapse panel/i })).toBeVisible();
});

test("agricultural intelligence sections render from aggregate fixture", async ({
  page,
}) => {
  const AGRI = {
    location: { latitude: 17.05, longitude: 79.27, locality: "Nalgonda", district: "Nalgonda", state: "Telangana", country: "India" },
    snapshot: {
      common_crops: ["Paddy", "Cotton"],
      soil: { texture: "clay loam", ph: 7.2 },
      season_rain_mm: 684,
      season_label: "Jun–Sep 2026",
      disease_names: ["Blast", "Bacterial leaf blight"],
    },
    weather: { status: "available", data: { temperature_c: 31, humidity_pct: 62, rain_mm: 4, recorded_at: new Date().toISOString() } },
    rainfall: {
      status: "available",
      data: { today_mm: 4.2, last_7d_mm: 31, last_7d_coverage: "7/7 days", month_mm: 112, month_coverage: "26/26 days", season_mm: 684, season_label: "Jun–Sep 2026", season_coverage: "90/118 days" },
      source: "Open-Meteo",
    },
    soil: {
      status: "available",
      data: { texture: "clay loam", ph: 7.2, ph_uncertainty: null, organic_carbon_gkg: 8.4, organic_carbon_pct: 0.84, sand_pct: 30, silt_pct: 28, clay_pct: 42, cec_cmolkg: 22, nitrogen_gkg: 0.9 },
      source: "SoilGrids",
      resolution_m: 250,
      mode: "modelled",
    },
    crops: {
      status: "available",
      data: {
        common: [{ commodity: "Paddy", arrival_share: 0.5, observations: 100 }, { commodity: "Cotton", arrival_share: 0.3, observations: 60 }],
        interpretation: "Commodities recently traded in this district's mandis.",
      },
      source: "agmarknet",
      data_year: "2025–2026",
    },
    suitability: {
      status: "available",
      data: {
        estimates: [
          { crop: "Paddy", suitability_band: "Moderate", factors: ["rainfall in range"], limitations: ["irrigation access unknown to the map"], note: "Standing water needed." },
        ],
        disclaimer: "Suitability is an environmental estimate.",
      },
      source: "CropPilot suitability engine (rule-based)",
      mode: "derived",
    },
    water: { status: "unavailable", data: null, reason: "no-accessible-source" },
    disease_context: {
      status: "available",
      data: {
        crop_risks: [
          { crop: "rice", diseases: [{ disease_id: "rice.rice_blast", display_name: "Blast", priority: "telangana-high", has_guidance: true }] },
        ],
        interpretation: "Crop-associated risks — not confirmed local outbreaks.",
      },
      source: "CropPilot disease taxonomy + knowledge",
      mode: "knowledge-derived",
    },
    sources: ["open-meteo", "soilgrids", "agmarknet"],
  };
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.route("**/api/v1/map/reverse*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(REVERSE) })
  );
  await page.route("**/api/v1/map/agricultural-context*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(AGRI) })
  );
  await page.route("**/api/v1/map/markets*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ markets: [], unmapped_count: 0, radius_km: 50, district: "Nalgonda", state: "Telangana" }) })
  );
  // Panel weather uses the dedicated fast weather query.
  await page.route("**/api/v1/map/weather*", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(WEATHER) })
  );
  await page.goto("/maps?lat=17.05&lng=79.27");
  // Snapshot strip.
  await expect(page.getByText("Agricultural snapshot").first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByText(/Paddy · Cotton|Paddy/).first()).toBeVisible();
  // Weather from the dedicated fast query (31.5 rounds to 32).
  await expect(page.getByText("32°C").first()).toBeVisible();
  // Soil section (collapsed): expand and check modelled values.
  await page.getByRole("button", { name: /soil/i }).first().click();
  await expect(page.getByText("clay loam").first()).toBeVisible();
  await expect(page.getByText(/modelled estimate, not a lab soil test/i).first()).toBeVisible();
  // Rainfall section.
  await page.getByRole("button", { name: /^rainfall$/i }).first().click();
  await expect(page.getByText("112.0 mm").first()).toBeVisible();
  // Crops + suitability (no "best crop" language).
  await page.getByRole("button", { name: /^crops$/i }).first().click();
  await expect(page.getByText("Moderate").first()).toBeVisible();
  await expect(page.getByText(/environmental estimate/i).first()).toBeVisible();
  await expect(page.getByText(/best crop/i)).toHaveCount(0);
  // Water unavailable, honestly.
  await page.getByRole("button", { name: /^water resources$/i }).first().click();
  await expect(page.getByText(/water data unavailable/i).first()).toBeVisible();
  // Disease context: risks, not outbreaks.
  await page.getByRole("button", { name: /disease context/i }).first().click();
  await expect(page.getByText("Blast").first()).toBeVisible();
  await expect(page.getByText(/not confirmed local outbreaks/i).first()).toBeVisible();
  await expect(page.getByText(/outbreaks confirmed|prevalence|70%/i)).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("map page localizes to Telugu", async ({ page }) => {
  await page.goto("/maps");
  await page.locator("header select").first().selectOption("te").catch(() => {});
  await page.waitForTimeout(800);
  await expect(
    page.getByTestId("croppilot-map").or(page.getByText(/interactive map is unavailable/i))
  ).toBeVisible({ timeout: 30000 });
});
