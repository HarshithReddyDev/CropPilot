"use client";

import { cn } from "@/lib/utils";
import { useTranslation, formatDate } from "@/lib/i18n";
import type { MarketFreshness } from "@/types";

export function FreshnessBadge({
  freshness,
  className,
}: {
  freshness?: MarketFreshness;
  className?: string;
}) {
  const { t, locale } = useTranslation();
  if (!freshness || !freshness.latest_observation_date) {
    return (
      <span
        className={cn(
          "inline-flex items-center rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground",
          className
        )}
      >
        {t("markets.freshNone")}
      </span>
    );
  }
  return (
    <span
      className={cn(
        "inline-flex flex-wrap items-center gap-x-2 rounded-full px-3 py-1 text-xs font-medium",
        freshness.is_stale
          ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
          : "bg-primary/10 text-primary",
        className
      )}
    >
      <span>
        {t("markets.freshLatest", { date: formatDate(locale, freshness.latest_observation_date) })}
      </span>
      {freshness.is_stale && <span>{t("markets.freshStale")}</span>}
    </span>
  );
}
