#!/usr/bin/env node
// V1.3 §52 localization validation: run `node scripts/check-i18n.mjs`.
// Fails on: unparseable locale files, key drift vs en, broken/missing
// {placeholders}, malformed Unicode (lone surrogates).

import { readFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const dir = join(dirname(fileURLToPath(import.meta.url)), "..", "i18n", "messages");
const files = readdirSync(dir).filter((f) => f.endsWith(".json"));

const read = (f) => JSON.parse(readFileSync(join(dir, f), "utf8"));
const en = read("en.json");

const flat = (obj, prefix = "") =>
  Object.entries(obj).flatMap(([k, v]) =>
    typeof v === "object" && v !== null
      ? flat(v, `${prefix}${k}.`)
      : [[`${prefix}${k}`, String(v)]]
  );

const enEntries = flat(en);
const enKeys = new Map(enEntries);
const placeholders = (s) => new Set([...s.matchAll(/\{([a-zA-Z0-9_]+)\}/g)].map((m) => m[1]));
const loneSurrogate = /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/;

let failures = 0;
const fail = (msg) => {
  failures += 1;
  console.error(`i18n FAIL: ${msg}`);
};

for (const f of files) {
  if (f === "en.json") continue;
  let data;
  try {
    data = read(f);
  } catch (e) {
    fail(`${f} does not parse: ${e.message}`);
    continue;
  }
  const got = new Map(flat(data));
  for (const [key, enText] of enKeys) {
    if (!got.has(key)) {
      fail(`${f} missing key: ${key}`);
      continue;
    }
    const text = got.get(key);
    const want = placeholders(enText);
    const have = placeholders(text);
    for (const p of want) {
      if (!have.has(p)) fail(`${f} ${key} drops placeholder {${p}}`);
    }
    if (loneSurrogate.test(text)) fail(`${f} ${key} has malformed Unicode`);
  }
  for (const key of got.keys()) {
    if (!enKeys.has(key)) fail(`${f} extra key (not in en): ${key}`);
  }
}

if (failures > 0) {
  console.error(`i18n: ${failures} failure(s)`);
  process.exit(1);
}
console.log(`i18n OK: ${files.join(", ")} — keys and placeholders match en.`);
