"use client";

import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";
import type { MarketProvenance } from "@/types";

export function SourceAttribution({
  provenance,
  compact = false,
  className,
}: {
  provenance?: MarketProvenance;
  compact?: boolean;
  className?: string;
}) {
  const { t } = useTranslation();
  if (!provenance) return null;
  if (compact) {
    return (
      <p className={cn("text-xs text-muted-foreground", className)}>
        {t("markets.sourceLabel", { name: provenance.name })}
      </p>
    );
  }
  return (
    <div className={cn("text-xs text-muted-foreground", className)}>
      <p>
        {t("markets.sourceLabel", { name: provenance.name })} {t("markets.sourceBody")}
      </p>
      <p className="mt-1 font-mono text-[11px] opacity-80">
        {t("markets.sourceResource", { id: provenance.resource_id })}
      </p>
    </div>
  );
}
