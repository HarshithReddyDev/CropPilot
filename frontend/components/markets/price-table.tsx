"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { ChevronUp, ChevronDown, Search, ChevronLeft, ChevronRight, ArrowUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTranslation, formatDate, formatNumber } from "@/lib/i18n";
import type { MarketPrice } from "@/types";

type SortField = keyof MarketPrice;
type SortDir = "asc" | "desc";

interface PriceTableProps {
  data: MarketPrice[];
  showState?: boolean;
}

function formatArrivals(item: MarketPrice, locale: string): string {
  if (item.arrivals == null) return "--";
  const qty = formatNumber(locale, Number(item.arrivals));
  return item.arrival_unit ? `${qty} ${item.arrival_unit}` : qty;
}

export function PriceTable({ data, showState = false }: PriceTableProps) {
  const { t, locale } = useTranslation();
  const [sortField, setSortField] = useState<SortField>("modal_price");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const perPage = 10;

  const filtered = useMemo(() => {
    if (!search.trim()) return data;
    const q = search.toLowerCase();
    return data.filter(
      (r) =>
        r.commodity.toLowerCase().includes(q) ||
        r.variety?.toLowerCase().includes(q) ||
        r.market.toLowerCase().includes(q) ||
        r.district?.toLowerCase().includes(q) ||
        r.state.toLowerCase().includes(q)
    );
  }, [data, search]);

  const sorted = useMemo(() => {
    const arr = [...filtered];
    arr.sort((a, b) => {
      let aVal: unknown = a[sortField];
      let bVal: unknown = b[sortField];
      if (typeof aVal === "string") aVal = aVal.toLowerCase();
      if (typeof bVal === "string") bVal = bVal.toLowerCase();
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (aVal < bVal) return sortDir === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
    return arr;
  }, [filtered, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / perPage));
  const paginated = sorted.slice((page - 1) * perPage, page * perPage);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("asc");
    }
    setPage(1);
  };

  const SortHeader = ({
    field,
    label,
    className,
  }: {
    field: SortField;
    label: string;
    className?: string;
  }) => (
    <button
      onClick={() => toggleSort(field)}
      className={cn(
        "flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors",
        sortField === field && "text-primary",
        className
      )}
    >
      {label}
      {sortField === field ? (
        sortDir === "asc" ? (
          <ChevronUp className="h-3 w-3" />
        ) : (
          <ChevronDown className="h-3 w-3" />
        )
      ) : (
        <ArrowUpDown className="h-3 w-3 opacity-40" />
      )}
    </button>
  );

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border p-4">
        <div className="relative flex-1">
          <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder={t("markets.tableSearch")}
            aria-label={t("markets.tableSearch")}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="h-9 w-full rounded-lg border border-input bg-background ps-9 pe-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="hidden w-full md:table">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-start"><SortHeader field="commodity" label={t("markets.commodity")} /></th>
              <th className="px-4 py-3 text-start"><SortHeader field="variety" label={t("markets.variety")} /></th>
              <th className="px-4 py-3 text-start"><SortHeader field="grade" label={t("markets.grade")} /></th>
              <th className="px-4 py-3 text-start"><SortHeader field="market" label={t("markets.market")} /></th>
              <th className="px-4 py-3 text-start"><SortHeader field="district" label={t("markets.district")} /></th>
              {showState && (
                <th className="px-4 py-3 text-start"><SortHeader field="state" label={t("markets.state")} /></th>
              )}
              <th className="px-4 py-3 text-end"><SortHeader field="min_price" label={t("markets.thMin")} /></th>
              <th className="px-4 py-3 text-end"><SortHeader field="max_price" label={t("markets.thMax")} /></th>
              <th className="px-4 py-3 text-end"><SortHeader field="modal_price" label={t("markets.thModal")} /></th>
              <th className="px-4 py-3 text-end"><SortHeader field="arrivals" label={t("markets.thArrivals")} /></th>
              <th className="px-4 py-3 text-end"><SortHeader field="arrival_date" label={t("markets.thObserved")} /></th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((item, i) => (
              <motion.tr
                key={item.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                className="border-b border-border/50 transition-colors hover:bg-muted/50"
              >
                <td className="px-4 py-3 text-sm font-medium text-foreground">{item.commodity}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{item.variety || "--"}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{item.grade || "--"}</td>
                <td className="px-4 py-3 text-sm text-foreground">{item.market}</td>
                <td className="px-4 py-3 text-sm text-muted-foreground">{item.district || "--"}</td>
                {showState && (
                  <td className="px-4 py-3 text-sm text-muted-foreground">{item.state}</td>
                )}
                <td className="px-4 py-3 text-end text-sm text-muted-foreground">{formatNumber(locale, item.min_price)}</td>
                <td className="px-4 py-3 text-end text-sm text-muted-foreground">{formatNumber(locale, item.max_price)}</td>
                <td className="px-4 py-3 text-end text-sm font-semibold text-foreground">{formatNumber(locale, item.modal_price)}</td>
                <td className="px-4 py-3 text-end text-sm text-muted-foreground">{formatArrivals(item, locale)}</td>
                <td className="px-4 py-3 text-end text-sm text-muted-foreground">{formatDate(locale, item.arrival_date)}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>

        <div className="flex flex-col gap-3 p-4 md:hidden">
          {paginated.map((item, i) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className="rounded-lg border border-border/50 bg-muted/30 p-3"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-foreground">{item.commodity}</p>
                  <p className="text-xs text-muted-foreground">
                    {[item.variety, item.grade].filter(Boolean).join(", ") || item.market}
                  </p>
                </div>
                <div className="text-end">
                  <p className="text-sm font-bold text-foreground">{t("markets.priceRs", { value: formatNumber(locale, item.modal_price) })}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(locale, item.arrival_date)}</p>
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                <span>{item.market}{item.district ? `, ${item.district}` : ""}{showState ? `, ${item.state}` : ""}</span>
                <span>{t("markets.minMaxLine", { min: formatNumber(locale, item.min_price), max: formatNumber(locale, item.max_price) })}</span>
              </div>
              {item.arrivals != null && (
                <p className="mt-1 text-xs text-muted-foreground">
                  {t("markets.arrivalsLine", { value: formatArrivals(item, locale) })}
                </p>
              )}
            </motion.div>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-border px-4 py-3">
        <p className="text-xs text-muted-foreground">
          {t("markets.showingCount", { from: (page - 1) * perPage + 1, to: Math.min(page * perPage, sorted.length), total: sorted.length })}
        </p>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            aria-label={t("markets.prevPage")}
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronLeft className="h-4 w-4 rtl:-scale-x-100" />
          </button>
          {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
            const start = Math.max(1, Math.min(page - 2, totalPages - 4));
            const p = start + i;
            if (p > totalPages) return null;
            return (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-md text-xs font-medium transition-colors",
                  p === page
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {p}
              </button>
            );
          })}
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
            aria-label={t("markets.nextPage")}
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronRight className="h-4 w-4 rtl:-scale-x-100" />
          </button>
        </div>
      </div>
    </div>
  );
}
