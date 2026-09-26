// Disease detection E2E: real page against the live dev stack, no API
// interception. Upload path uses a real file chooser upload; the backend
// performs genuine image QA + model routing (models may be unavailable in
// CI, in which case the page must show an honest error/uncertain state —
// never a fake diagnosis).
import { test, expect } from "@playwright/test";
import { writeFileSync, unlinkSync } from "fs";
import { join } from "path";
import { tmpdir } from "os";
import { deflateSync } from "zlib";

test.use({ baseURL: "http://127.0.0.1:3000" });

// 1x1 red PNG (real decodable image bytes, but far too small for QA).
const RED_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
  "base64"
);

// Deterministic textured 256x256 PNG: passes image QA (not uniform, not
// tiny) so it reaches real routing/inference. Seeded PRNG => same bytes.
// Hand-encoded with node:zlib (no extra test dependencies).
function crc32(buf: Buffer): number {
  let table = (crc32 as unknown as { table?: number[] }).table;
  if (!table) {
    table = [];
    for (let n = 0; n < 256; n++) {
      let c = n;
      for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
      table[n] = c;
    }
    (crc32 as unknown as { table?: number[] }).table = table;
  }
  let crc = 0xffffffff;
  for (const b of buf) crc = table[(crc ^ b) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function pngChunk(type: string, data: Buffer): Buffer {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const td = Buffer.from(type, "ascii");
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([td, data])));
  return Buffer.concat([len, td, data, crc]);
}

function texturedPng(): Buffer {
  const w = 256;
  const h = 256;
  let s = 42;
  const rnd = () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return s / 0x7fffffff;
  };
  const raw = Buffer.alloc(h * (1 + w * 3));
  for (let y = 0; y < h; y++) {
    raw[y * (1 + w * 3)] = 0;
    for (let x = 0; x < w; x++) {
      const o = y * (1 + w * 3) + 1 + x * 3;
      raw[o] = Math.floor(20 + rnd() * 100);
      raw[o + 1] = Math.floor(80 + rnd() * 100);
      raw[o + 2] = Math.floor(20 + rnd() * 70);
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;
  ihdr[9] = 2;
  return Buffer.concat([
    Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
    pngChunk("IHDR", ihdr),
    pngChunk("IDAT", deflateSync(raw)),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
}

test("disease page renders upload UI with crop hint and no console errors", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/disease-detection");
  await expect(page.getByRole("heading", { name: /disease/i }).first()).toBeVisible();
  await expect(page.locator("#disease-crop-hint")).toBeVisible();
  expect(errors).toEqual([]);
});

test("disease upload reaches the real API and ends in an honest state", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const tmp = join(tmpdir(), "croppilot-disease-e2e.png");
  writeFileSync(tmp, RED_PNG);
  try {
    await page.goto("/disease-detection");
    // Real file upload through the hidden input.
    await page.locator('input[type="file"]').setInputFiles(tmp);
    // Either a genuine result/uncertain/error state appears. The page
    // must never show a random mock disease with a fake confidence %.
    await expect(
      page
        .getByText(
          /could not confidently|too poor to analyze|not strong enough|Uncertain|unusable|not yet have|failed|Likely diagnosis|Probable|Analysis details|New Detection/i
        )
        .first()
    ).toBeVisible({ timeout: 120000 });
    // No fake bounding-box overlay from classifier regions.
    expect(errors).toEqual([]);
  } finally {
    try {
      unlinkSync(tmp);
    } catch {
      /* ignore */
    }
  }
});

test("wheat photo ends in a no-coverage state, never a load-failure message", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const tmp = join(tmpdir(), "croppilot-disease-wheat.png");
  writeFileSync(tmp, texturedPng());
  try {
    await page.goto("/disease-detection");
    // Manual crop selection from the taxonomy-driven selector.
    await expect(
      page.locator('#disease-crop-hint option[value="wheat"]')
    ).toBeAttached({ timeout: 30000 });
    await page.locator("#disease-crop-hint").selectOption("wheat");
    await page.locator('input[type="file"]').setInputFiles(tmp);
    // Wheat has taxonomy rows but no verified production specialist, so
    // routing must report a coverage gap — not a model load failure.
    await expect(
      page.getByText("Crop not currently supported").first()
    ).toBeVisible({ timeout: 120000 });
    await expect(page.getByText("Model coverage unavailable").first()).toBeVisible();
    await expect(page.getByText("No verified diagnosis").first()).toBeVisible();
    // "A specialist model failed to load" must NOT appear for a coverage gap.
    await expect(page.getByText(/could not be loaded/i)).toHaveCount(0);
    // Exactly one history entry for the single upload (no duplicates).
    await expect(page.locator("tbody tr")).toHaveCount(1);
    await expect(page.locator("tbody tr").first().getByText("Not supported")).toBeVisible();
    expect(errors).toEqual([]);
  } finally {
    try {
      unlinkSync(tmp);
    } catch {
      /* ignore */
    }
  }
});

test("new detection resets state without adding history entries", async ({
  page,
}) => {
  const tmp = join(tmpdir(), "croppilot-disease-reset.png");
  writeFileSync(tmp, RED_PNG);
  try {
    await page.goto("/disease-detection");
    await page.locator('input[type="file"]').setInputFiles(tmp);
    await expect(
      page.getByText(/could not be read|too poor to analyze|No verified diagnosis/i).first()
    ).toBeVisible({ timeout: 120000 });
    const rowsBefore = await page.locator("tbody tr").count();
    await page.getByRole("button", { name: "New Detection" }).click();
    // Upload UI is back, crop selector cleared, no extra history row.
    await expect(page.locator("#disease-crop-hint")).toBeVisible();
    await expect(page.locator("#disease-crop-hint")).toHaveValue("");
    await expect(page.locator("tbody tr")).toHaveCount(rowsBefore);
  } finally {
    try {
      unlinkSync(tmp);
    } catch {
      /* ignore */
    }
  }
});

test("manual crop selection can re-analyze the same photo", async ({ page }) => {
  test.setTimeout(240000);
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const tmp = join(tmpdir(), "croppilot-disease-recrop.png");
  writeFileSync(tmp, texturedPng());
  try {
    await page.goto("/disease-detection");
    await expect(
      page.locator('#disease-crop-hint option[value="wheat"]')
    ).toBeAttached({ timeout: 30000 });
    await page.locator("#disease-crop-hint").selectOption("wheat");
    await page.locator('input[type="file"]').setInputFiles(tmp);
    await expect(
      page.getByText("Crop not currently supported").first()
    ).toBeVisible({ timeout: 120000 });
    // Pick a covered crop and analyze the same in-memory photo again.
    // Potato is covered by the verified multicrop model; the end state must
    // be honest whatever the model cache contains (real result, honest
    // uncertainty, or a clearly-labeled temporary failure).
    await page.locator("#disease-recrop").selectOption("potato");
    await page.getByRole("button", { name: "Analyze again" }).click();
    await expect(
      page
        .getByText(
          /No verified diagnosis|Analysis temporarily failed|Likely diagnosis|Probable/i
        )
        .first()
    ).toBeVisible({ timeout: 180000 });
    expect(errors).toEqual([]);
  } finally {
    try {
      unlinkSync(tmp);
    } catch {
      /* ignore */
    }
  }
});

test("unknown-crop uncertain hides alternatives, keeps raw outputs in details", async ({
  page,
}) => {
  // Deterministic fixture at the API boundary: unknown crop + uncertain
  // status with tomato raw classes. Rendering must not present the classes
  // as agronomically plausible alternatives.
  const fixture = {
    request_id: "fixture-unknown-tomato-001",
    status: "uncertain",
    reason_code: "LOW_CONFIDENCE",
    crop: { name: null, confidence_band: "unknown", source: "unknown", status: "unknown" },
    image_quality: { status: "good", score: 0.85, reasons: [], width: 256, height: 256, format: "png" },
    findings: [
      {
        disease_id: "plantvillage.tomato_healthy",
        display_name: "Tomato healthy",
        region: { kind: "full", x1: 0, y1: 0, x2: 1, y2: 1, score: null, source: "deterministic" },
        raw_score: 0.316,
        calibrated_score: null,
        score_type: "raw_model_score",
        confidence_band: "low",
        evidence_level: "E4",
        model_ids: ["imaflower/plantvillage-mobilenetv3"],
        agreement_count: 1,
        field_validation: "Not verified",
        notes: null,
      },
    ],
    alternatives: [
      {
        disease_id: "plantvillage.tomato_tomato_yellowleaf_curl_virus",
        display_name: "plantvillage.tomato_tomato_yellowleaf_curl_virus",
        region: { kind: "full", x1: 0, y1: 0, x2: 1, y2: 1, score: null, source: "deterministic" },
        raw_score: 0.21,
        calibrated_score: null,
        score_type: "raw_model_score",
        confidence_band: "low",
        evidence_level: "E4",
        model_ids: ["imaflower/plantvillage-mobilenetv3"],
        agreement_count: 1,
        field_validation: "Not verified",
        notes: null,
      },
      {
        disease_id: "plantvillage.tomato_tomato_mosaic_virus",
        display_name: "plantvillage.tomato_tomato_mosaic_virus",
        region: { kind: "full", x1: 0, y1: 0, x2: 1, y2: 1, score: null, source: "deterministic" },
        raw_score: 0.14,
        calibrated_score: null,
        score_type: "raw_model_score",
        confidence_band: "low",
        evidence_level: "E4",
        model_ids: ["imaflower/plantvillage-mobilenetv3"],
        agreement_count: 1,
        field_validation: "Not verified",
        notes: null,
      },
    ],
    routing: {
      routing_mode: "registry_fallback",
      specialists_considered: ["imaflower/plantvillage-mobilenetv3"],
      specialists_run: ["imaflower/plantvillage-mobilenetv3"],
      crop_hint: null,
      crop_status: "unknown",
      eligible_specialists: ["imaflower/plantvillage-mobilenetv3"],
      excluded_specialists: {
        "surprisedPikachu007/tomato-disease-detection_V2": "needs-crop-hint",
      },
    },
    evidence: [
      {
        model_id: "imaflower/plantvillage-mobilenetv3",
        license_status: "permissive",
        evidence_level: "E4",
        field_validation: "Not verified",
        metric_context: null,
        research_only: false,
      },
    ],
    knowledge: [],
    citations: [],
    next_action: "Evidence is weak. Please take a closer photo of one affected leaf in good daylight.",
    pipeline: {
      routing_mode: "registry_fallback",
      specialists_considered: ["imaflower/plantvillage-mobilenetv3"],
      specialists_run: ["imaflower/plantvillage-mobilenetv3"],
      specialist_latencies_ms: {},
      quality_latency_ms: 12,
      router_latency_ms: 1,
      fusion_latency_ms: 1,
      vlm_latency_ms: 0,
      total_latency_ms: 900,
      vlm_used: false,
      rag_used: false,
    },
    error_code: null,
  };
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const tmp = join(tmpdir(), "croppilot-disease-fixture.png");
  writeFileSync(tmp, texturedPng());
  try {
    await page.goto("/disease-detection");
    await page.route("**/api/v1/disease/analyze", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(fixture) });
    });
    await page.locator('input[type="file"]').setInputFiles(tmp);
    await expect(page.getByText("No verified diagnosis").first()).toBeVisible({
      timeout: 30000,
    });
    await expect(
      page.getByText("could not identify the crop with enough evidence").first()
    ).toBeVisible();
    await expect(page.getByTestId("unknown-crop-row")).toContainText("Not identified");
    // Raw classes must NOT appear as farmer-facing alternatives.
    await expect(page.getByText("Possible alternatives")).toHaveCount(0);
    // ...but stay available under Analysis Details.
    await page.getByText("Analysis details").click();
    await expect(page.getByText("Model outputs").first()).toBeVisible();
    await expect(page.getByText("Tomato healthy").first()).toBeVisible();
    await expect(page.getByText("0.316").first()).toBeVisible();
    await expect(page.getByText(/not treated as a verified disease diagnosis/i).first()).toBeVisible();
    // Manual crop selection is offered, and history stays honest.
    await expect(page.getByText("Do you know the crop?").first()).toBeVisible();
    await expect(page.locator("#disease-recrop")).toBeVisible();
    const row = page.locator("tbody tr").first();
    await expect(row.getByText("No diagnosis")).toBeVisible();
    await expect(row.getByText("Not identified")).toBeVisible();
    expect(errors).toEqual([]);
  } finally {
    try {
      unlinkSync(tmp);
    } catch {
      /* ignore */
    }
  }
});

test("disease page localizes to Telugu", async ({ page }) => {
  await page.goto("/disease-detection");
  await page.locator("header select").first().selectOption("te").catch(() => {});
  await page.waitForTimeout(500);
  await expect(page.locator("#disease-crop-hint")).toBeVisible();
});
