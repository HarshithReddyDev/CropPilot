"use client";

import { useMemo } from "react";
import { useTranslation, formatDate, formatNumber } from "@/lib/i18n";
import type { MarketComparisonRow } from "@/types";

function groupKey(r: MarketComparisonRow): string {
  return `${r.variety ?? ""}||${r.grade ?? ""}||${r.price_per_unit}`;
}

function groupLabel(t: (key: string) => string, r: MarketComparisonRow): string {
  const parts = [r.variety, r.grade].filter((p) => p && p.trim() !== "");
  const name = parts.length > 0 ? parts.join(", ") : t("markets.cmpUnspecified");
  return `${name} (${r.price_per_unit})`;
}

export function MarketComparison({ rows }: { rows: MarketComparisonRow[] }) {
  const { t, locale } = useTranslation();
  const groups = useMemo(() => {
    const map = new Map<string, MarketComparisonRow[]>();
    for (const row of rows) {
      const key = groupKey(row);
      const list = map.get(key) ?? [];
      list.push(row);
      map.set(key, list);
    }
    return [...map.entries()].map(([key, list]) => ({
      key,
      label: groupLabel(t, list[0]),
      rows: [...list].sort((a, b) => a.modal_price - b.modal_price),
    }));
  }, [rows, t]);

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 text-center">
        <p className="text-sm font-medium text-foreground">{t("markets.cmpNoData")}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          {t("markets.cmpNoDataBody")}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="border-b border-border p-4">
        <h3 className="text-sm font-semibold text-foreground">{t("markets.cmpTitle")}</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          {t("markets.cmpBody")}
        </p>
      </div>
      <div className="space-y-6 p-4">
        {groups.map((group) => (
          <div key={group.key}>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {group.label}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-3 py-2 text-start text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {t("markets.market")}
                    </th>
                    <th className="px-3 py-2 text-start text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {t("markets.district")}
                    </th>
                    <th className="px-3 py-2 text-start text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {t("markets.state")}
                    </th>
                    <th className="px-3 py-2 text-end text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {t("markets.thModal")}
                    </th>
                    <th className="px-3 py-2 text-end text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {t("markets.cmpMinMax")}
                    </th>
                    <th className="px-3 py-2 text-end text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {t("markets.thArrivals")}
                    </th>
                    <th className="px-3 py-2 text-end text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      {t("markets.thObserved")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {group.rows.map((row) => (
                    <tr
                      key={`${row.state}-${row.district}-${row.market}-${row.arrival_date}`}
                      className="border-b border-border/50 last:border-0"
                    >
                      <td className="px-3 py-2 text-sm font-medium text-foreground">
                        {row.market}
                      </td>
                      <td className="px-3 py-2 text-sm text-muted-foreground">
                        {row.district || "--"}
                      </td>
                      <td className="px-3 py-2 text-sm text-muted-foreground">
                        {row.state}
                      </td>
                      <td className="px-3 py-2 text-end text-sm font-semibold text-foreground">
                        {formatNumber(locale, row.modal_price)}
                      </td>
                      <td className="px-3 py-2 text-end text-sm text-muted-foreground">
                        {formatNumber(locale, row.min_price)} to{" "}
                        {formatNumber(locale, row.max_price)}
                      </td>
                      <td className="px-3 py-2 text-end text-sm text-muted-foreground">
                        {row.arrivals != null
                          ? `${formatNumber(locale, Number(row.arrivals))}${row.arrival_unit ? ` ${row.arrival_unit}` : ""}`
                          : "--"}
                      </td>
                      <td className="px-3 py-2 text-end text-sm text-muted-foreground">
                        {formatDate(locale, row.arrival_date)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
