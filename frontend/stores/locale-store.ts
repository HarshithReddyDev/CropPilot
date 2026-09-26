import { create } from "zustand";
import { persist } from "zustand/middleware";
import { LOCALES } from "@/lib/languages";

export type AppLocale = string;
export const DEFAULT_LOCALE = "en";
const STORE_KEY = "croppilot-locale";

const KNOWN = new Set(LOCALES.map((l) => l.code));

function sanitize(code: unknown): string {
  return typeof code === "string" && KNOWN.has(code) ? code : DEFAULT_LOCALE;
}

function browserLocale(): string | null {
  if (typeof navigator === "undefined") return null;
  const tag = (navigator.language || "").toLowerCase();
  const short = tag.split("-")[0];
  if (KNOWN.has(short)) return short;
  const prefix = LOCALES.find((l) => tag.startsWith(l.code))?.code;
  return prefix ?? null;
}

interface LocaleState {
  locale: AppLocale;
  explicit: boolean;
  setLocale: (locale: AppLocale, explicit?: boolean) => void;
  initFromBrowser: () => void;
}

export const useLocaleStore = create<LocaleState>()(
  persist(
    (set, get) => ({
      locale: DEFAULT_LOCALE,
      explicit: false,
      setLocale: (locale, explicit = true) =>
        set({ locale: sanitize(locale), explicit }),
      // Explicit user preference always wins: only adopt the browser
      // language when the user never chose one.
      initFromBrowser: () => {
        const { explicit } = get();
        if (explicit) return;
        const detected = browserLocale();
        if (detected) set({ locale: detected });
      },
    }),
    {
      name: STORE_KEY,
      partialize: (s) => ({ locale: s.locale, explicit: s.explicit }),
    }
  )
);
