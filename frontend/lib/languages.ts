// Canonical locale list (V1.3 §3). Mirrors
// backend/services/assistant/languages.py — parity enforced by
// backend/tests/test_locale_parity.py. Do not edit names here alone:
// update the backend registry first, then mirror.

export interface LocaleInfo {
  code: string;
  locale: string;
  englishName: string;
  nativeName: string;
  script: string;
  rtl: boolean;
}

export const LOCALES: LocaleInfo[] = [
  { code: "en", locale: "en-IN", englishName: "English", nativeName: "English", script: "Latin", rtl: false },
  { code: "as", locale: "as-IN", englishName: "Assamese", nativeName: "অসমীয়া", script: "Bengali", rtl: false },
  { code: "bn", locale: "bn-IN", englishName: "Bengali", nativeName: "বাংলা", script: "Bengali", rtl: false },
  { code: "brx", locale: "brx-IN", englishName: "Bodo", nativeName: "बड़ो", script: "Devanagari", rtl: false },
  { code: "doi", locale: "doi-IN", englishName: "Dogri", nativeName: "डोगरी", script: "Devanagari", rtl: false },
  { code: "gu", locale: "gu-IN", englishName: "Gujarati", nativeName: "ગુજરાતી", script: "Gujarati", rtl: false },
  { code: "hi", locale: "hi-IN", englishName: "Hindi", nativeName: "हिन्दी", script: "Devanagari", rtl: false },
  { code: "kn", locale: "kn-IN", englishName: "Kannada", nativeName: "ಕನ್ನಡ", script: "Kannada", rtl: false },
  { code: "ks", locale: "ks-IN", englishName: "Kashmiri", nativeName: "کٲشُر", script: "Arabic", rtl: true },
  { code: "kok", locale: "kok-IN", englishName: "Konkani", nativeName: "कोंकणी", script: "Devanagari", rtl: false },
  { code: "mai", locale: "mai-IN", englishName: "Maithili", nativeName: "मैथिली", script: "Devanagari", rtl: false },
  { code: "ml", locale: "ml-IN", englishName: "Malayalam", nativeName: "മലയാളം", script: "Malayalam", rtl: false },
  { code: "mni", locale: "mni-IN", englishName: "Manipuri", nativeName: "মণিপুরী", script: "Bengali", rtl: false },
  { code: "mr", locale: "mr-IN", englishName: "Marathi", nativeName: "मराठी", script: "Devanagari", rtl: false },
  { code: "ne", locale: "ne-IN", englishName: "Nepali", nativeName: "नेपाली", script: "Devanagari", rtl: false },
  { code: "or", locale: "or-IN", englishName: "Odia", nativeName: "ଓଡ଼ିଆ", script: "Odia", rtl: false },
  { code: "pa", locale: "pa-IN", englishName: "Punjabi", nativeName: "ਪੰਜਾਬੀ", script: "Gurmukhi", rtl: false },
  { code: "sa", locale: "sa-IN", englishName: "Sanskrit", nativeName: "संस्कृतम्", script: "Devanagari", rtl: false },
  { code: "sat", locale: "sat-IN", englishName: "Santali", nativeName: "ᱥᱟᱱᱛᱟᱲᱤ", script: "Ol Chiki", rtl: false },
  { code: "sd", locale: "sd-IN", englishName: "Sindhi", nativeName: "سنڌي", script: "Arabic", rtl: true },
  { code: "ta", locale: "ta-IN", englishName: "Tamil", nativeName: "தமிழ்", script: "Tamil", rtl: false },
  { code: "te", locale: "te-IN", englishName: "Telugu", nativeName: "తెలుగు", script: "Telugu", rtl: false },
  { code: "ur", locale: "ur-IN", englishName: "Urdu", nativeName: "اردو", script: "Arabic", rtl: true },
];

// Locales with a shipped message catalog. Others fall back to English
// (honest fallback, never fabricated strings).
// UI catalogs currently present and parity-validated in i18n/messages.
// Keep canonical LOCALES separately for backend, ASR and TTS capabilities.
export const SHIPPED_CATALOGS = [
  "en", "te", "hi", "ta", "bn", "mr", "gu", "ne", "pa", "ur", "sa",
] as const;

export type ShippedLocale = (typeof SHIPPED_CATALOGS)[number];

export function isShippedCatalog(code: string): code is ShippedLocale {
  return (SHIPPED_CATALOGS as readonly string[]).includes(code);
}

export function effectiveUiLocale(code: string): ShippedLocale {
  return isShippedCatalog(code) ? code : "en";
}

export function localeInfo(code: string): LocaleInfo {
  return LOCALES.find((l) => l.code === code) ?? LOCALES[0];
}

export function isRtl(code: string): boolean {
  return localeInfo(code).rtl;
}
