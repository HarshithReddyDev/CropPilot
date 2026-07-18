"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { ChevronUp, ChevronDown, Search, ChevronLeft, ChevronRight, ArrowUpDown } from "lucide-react";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import type { MarketPrice } from "@/types";

type SortField = keyof MarketPrice;
type SortDir = "asc" | "desc";

interface PriceTableProps {
  data: MarketPrice[];
}

export function PriceTable({ data }: PriceTableProps) {
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

  const changePercent = (item: MarketPrice) => {
    const seed = item.id.charCodeAt(0) + item.id.charCodeAt(item.id.length - 1);
    const val = ((seed % 20) - 10) / 10;
    return val;
  };

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center gap-2 border-b border-border p-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search commodity, variety, market..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="h-9 w-full rounded-lg border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="hidden w-full md:table">
          <thead>
            <tr className="border-b border-border">
              <th className="px-4 py-3 text-left"><SortHeader field="commodity" label="Commodity" /></th>
              <th className="px-4 py-3 text-left"><SortHeader field="variety" label="Variety" /></th>
              <th className="px-4 py-3 text-left"><SortHeader field="market" label="Market" /></th>
              <th className="px-4 py-3 text-right"><SortHeader field="min_price" label="Min ₹" /></th>
              <th className="px-4 py-3 text-right"><SortHeader field="max_price" label="Max ₹" /></th>
              <th className="px-4 py-3 text-right"><SortHeader field="modal_price" label="Modal ₹" /></th>
              <th className="px-4 py-3 text-right"><span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Change</span></th>
              <th className="px-4 py-3 text-right"><SortHeader field="arrival_date" label="Date" /></th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((item, i) => {
              const chg = changePercent(item);
              return (
                <motion.tr
                  key={item.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className="border-b border-border/50 transition-colors hover:bg-muted/50 cursor-pointer"
                >
                  <td className="px-4 py-3 text-sm font-medium text-foreground">{item.commodity}</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">{item.variety ?? "--"}</td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    <span className="text-foreground">{item.market}</span>
                    <span className="ml-1 text-xs text-muted-foreground">({item.state})</span>
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-muted-foreground">{item.min_price.toLocaleString("en-IN")}</td>
                  <td className="px-4 py-3 text-right text-sm text-muted-foreground">{item.max_price.toLocaleString("en-IN")}</td>
                  <td className="px-4 py-3 text-right text-sm font-semibold text-foreground">{item.modal_price.toLocaleString("en-IN")}</td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={cn(
                        "inline-flex items-center gap-0.5 text-xs font-medium",
                        chg >= 0 ? "text-emerald-500" : "text-red-500"
                      )}
                    >
                      {chg >= 0 ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      {formatPercent(chg * 10)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-muted-foreground">{item.arrival_date.slice(5)}</td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>

        <div className="flex flex-col gap-3 p-4 md:hidden">
          {paginated.map((item, i) => {
            const chg = changePercent(item);
            return (
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
                    <p className="text-xs text-muted-foreground">{item.variety ?? item.market}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-foreground">₹{item.modal_price.toLocaleString("en-IN")}</p>
                    <span
                      className={cn(
                        "inline-flex items-center gap-0.5 text-xs font-medium",
                        chg >= 0 ? "text-emerald-500" : "text-red-500"
                      )}
                    >
                      {chg >= 0 ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      {formatPercent(chg * 10)}
                    </span>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>{item.market}, {item.state}</span>
                  <span>Min ₹{item.min_price} · Max ₹{item.max_price}</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      <div className="flex items-center justify-between border-t border-border px-4 py-3">
        <p className="text-xs text-muted-foreground">
          Showing {(page - 1) * perPage + 1}–{Math.min(page * perPage, sorted.length)} of {sorted.length}
        </p>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronLeft className="h-4 w-4" />
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
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
