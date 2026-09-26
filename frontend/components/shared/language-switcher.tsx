"use client";

import { useEffect } from "react";
import { Languages } from "lucide-react";
import { useLocaleStore, type AppLocale } from "@/stores/locale-store";
import { LOCALES, effectiveUiLocale, isRtl, isShippedCatalog } from "@/lib/languages";
import { loadLocale, useTranslation } from "@/lib/i18n";

export function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { t } = useTranslation();
  const { locale, setLocale, initFromBrowser } = useLocaleStore();

  useEffect(() => {
    initFromBrowser();
  }, [initFromBrowser]);

  useEffect(() => {
    let active = true;
    void loadLocale(locale as AppLocale).then((effectiveLocale) => {
      if (!active) return;
      document.documentElement.lang = effectiveLocale;
      document.documentElement.dir = isRtl(effectiveLocale) ? "rtl" : "ltr";
    });
    return () => {
      active = false;
    };
  }, [locale]);

  const availableLocales = LOCALES.filter((l) => isShippedCatalog(l.code));
  return (
    <label className="inline-flex items-center gap-1.5" aria-label={t("common.language")}>
      <Languages className="h-4 w-4 shrink-0" aria-hidden="true" />
      <span className="sr-only">{t("common.language")}</span>
      <select
        value={effectiveUiLocale(locale)}
        onChange={(e) => setLocale(e.target.value as AppLocale)}
        className="bg-transparent text-sm font-medium focus:outline-none cursor-pointer max-w-[9rem]"
        aria-label={t("common.selectLanguage")}
      >
        {availableLocales.map((l) => (
          <option key={l.code} value={l.code}>
            {l.nativeName}
          </option>
        ))}
      </select>
    </label>
  );
}
