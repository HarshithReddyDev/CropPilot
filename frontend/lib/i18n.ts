// Minimal locale runtime (V1.3 §1): same routes, persisted locale,
// per-locale JSON loaded lazily. Zero new dependencies.

import { useCallback, useEffect, useState } from "react";
import en from "@/i18n/messages/en.json";
import { useLocaleStore, type AppLocale } from "@/stores/locale-store";
import { effectiveUiLocale, type ShippedLocale } from "@/lib/languages";

type Dict = Record<string, Record<string, string>>;

// Shipped catalogs are tiny (~2 KB each): static import, no async flash,
// no dynamic-import failure mode. LOADERS below activate only for future
// locales (lazy per-locale chunks, §43).
const STATIC_DICTS: Partial<Record<ShippedLocale, Dict>> = {
  en: en as Dict,
};

const LOADERS: Partial<Record<ShippedLocale, () => Promise<{ default: Dict }>>> = {
  te: () => import("@/i18n/messages/te.json"),
  hi: () => import("@/i18n/messages/hi.json"),
  ta: () => import("@/i18n/messages/ta.json"),
  bn: () => import("@/i18n/messages/bn.json"),
  mr: () => import("@/i18n/messages/mr.json"),
  gu: () => import("@/i18n/messages/gu.json"),
  ne: () => import("@/i18n/messages/ne.json"),
  pa: () => import("@/i18n/messages/pa.json"),
  ur: () => import("@/i18n/messages/ur.json"),
  sa: () => import("@/i18n/messages/sa.json"),
};

const cache: Partial<Record<ShippedLocale, Dict>> = { en: en as Dict };

/** Load an actually shipped UI catalog. Unsupported/failed catalogs
 * resolve to English; English is never cached under another locale ID. */
export async function loadLocale(locale: AppLocale): Promise<ShippedLocale> {
  const target = effectiveUiLocale(locale);
  if (cache[target]) return target;
  const loader = LOADERS[target];
  if (!loader) return "en";
  try {
    const module = await loader();
    cache[target] = module.default;
    return target;
  } catch {
    return "en";
  }
}

export function translate(
  locale: AppLocale,
  key: string,
  vars?: Record<string, string | number>
): string {
  const target = effectiveUiLocale(locale);
  const selected = cache[target] ?? (STATIC_DICTS.en as Dict);
  const [namespace, ...rest] = key.split(".");
  const leaf = rest.join(".");
  const text = selected[namespace]?.[leaf]
    ?? (STATIC_DICTS.en as Dict)[namespace]?.[leaf]
    ?? key;

  if (!vars) return text;
  return Object.entries(vars).reduce(
    (out, [k, v]) => out.replaceAll(`{${k}}`, String(v)),
    text
  );
}

export function useTranslation() {
  const requestedLocale = useLocaleStore((state) => state.locale);
  const [resolution, setResolution] = useState<{
    requested: AppLocale;
    effective: ShippedLocale;
  }>(() => ({
    requested: requestedLocale,
    effective: effectiveUiLocale(requestedLocale),
  }));

  const locale = resolution.requested === requestedLocale
    ? resolution.effective
    : effectiveUiLocale(requestedLocale);

  useEffect(() => {
    let active = true;
    void loadLocale(requestedLocale).then((effective) => {
      if (active) setResolution({ requested: requestedLocale, effective });
    });
    return () => {
      active = false;
    };
  }, [requestedLocale]);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) =>
      translate(locale, key, vars),
    [locale]
  );

  return { t, locale };
}

export function bcp47(locale: AppLocale): string {
  return `${locale}-IN`;
}

export function formatDate(locale: AppLocale, input: string | Date): string {
  const date = input instanceof Date ? input : new Date(`${input}T00:00:00`);
  if (Number.isNaN(date.getTime())) return String(input);
  return new Intl.DateTimeFormat(bcp47(locale), {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}

export function formatNumber(locale: AppLocale, value: number): string {
  return new Intl.NumberFormat(bcp47(locale), {
    maximumFractionDigits: 2,
  }).format(value);
}

/** Display label mapping for canonical market values. Canonical values
 *  are NEVER translated for backend use; labels are display-only, and
 *  unknown values fall back to the canonical string itself. */
const COMMODITY_LABELS: Record<string, Partial<Record<AppLocale, string>>> = {
  "Paddy(Common)": { te: "వరి (సాధారణ)", hi: "धान (सामान्य)" },
  Tomato: { te: "టమాటా", hi: "टमाटर" },
  Wheat: { te: "గోధుమ", hi: "गेहूं" },
  Cotton: { te: "పత్తి", hi: "कपास" },
};

export function displayCommodity(canonical: string, locale: AppLocale): string {
  if (locale === "en") return canonical;
  return COMMODITY_LABELS[canonical]?.[locale] ?? displayCrop(canonical, locale);
}

/** Canonical crop display dictionary (catalog `crops.*`, display-only).
 *  Normalizes "Paddy(Common)" -> paddy etc.; unknown values pass through
 *  unchanged (never mutate identifiers). */
export function displayCrop(canonical: string, locale: AppLocale): string {
  if (locale === "en") return canonical;
  const key = canonical
    .toLowerCase()
    .replace(/\(.*?\)/g, "")
    .trim()
    .replace(/\s+/g, "");
  const map: Record<string, string> = {
    rice: "crops.rice",
    paddy: "crops.paddy",
    wheat: "crops.wheat",
    cotton: "crops.cotton",
    maize: "crops.maize",
    corn: "crops.maize",
    sugarcane: "crops.sugarcane",
    tomato: "crops.tomato",
    potato: "crops.potato",
    onion: "crops.onion",
    soybean: "crops.soybean",
    soya: "crops.soybean",
    groundnut: "crops.groundnut",
    peanut: "crops.groundnut",
    chilli: "crops.chilli",
    chili: "crops.chilli",
  };
  const ck = map[key];
  if (!ck) return canonical;
  const hit = translate(locale, ck);
  return hit === ck ? canonical : hit;
}

/** Locale-aware short month names (Jan-Dec order) for charts. */
export function shortMonths(locale: AppLocale): string[] {
  const fmt = new Intl.DateTimeFormat(bcp47(locale), { month: "short" });
  return Array.from({ length: 12 }, (_, m) => fmt.format(new Date(2026, m, 1)));
}
