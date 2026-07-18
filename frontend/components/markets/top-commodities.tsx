"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { CHART_COLORS } from "@/lib/constants";
import { Sparkline } from "./sparkline";
import type { MarketPrice } from "@/types";

interface TopCommoditiesProps {
  data: MarketPrice[];
}

export function TopCommodities({ data }: TopCommoditiesProps) {
  const commodityStats = useMemo(() => {
    const grouped: Record<string, { prices: number[]; varieties: string[] }> = {};
    for (const item of data) {
      if (!grouped[item.commodity]) {
        grouped[item.commodity] = { prices: [], varieties: [] };
      }
      grouped[item.commodity].prices.push(item.modal_price);
      if (item.variety && !grouped[item.commodity].varieties.includes(item.variety)) {
        grouped[item.commodity].varieties.push(item.variety);
      }
    }

    return Object.entries(grouped)
      .map(([name, stats]) => {
        const avgPrice =
          stats.prices.reduce((a, b) => a + b, 0) / stats.prices.length;
        const firstPrice = stats.prices[0];
        const lastPrice = stats.prices[stats.prices.length - 1];
        const change = firstPrice > 0 ? ((lastPrice - firstPrice) / firstPrice) * 100 : 0;
        return { name, avgPrice, change, prices: stats.prices };
      })
      .sort((a, b) => b.change - a.change);
  }, [data]);

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <h3 className="mb-3 text-sm font-semibold text-foreground">Top Commodities</h3>
      <div className="space-y-2">
        {commodityStats.map((c, i) => (
          <motion.div
            key={c.name}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            className="flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-muted/50"
          >
            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-muted text-[10px] font-bold text-muted-foreground">
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-foreground truncate">{c.name}</p>
              <p className="text-xs text-muted-foreground">{formatCurrency(c.avgPrice)}</p>
            </div>
            <div className="w-16 h-8">
              <Sparkline data={c.prices} color={c.change >= 0 ? CHART_COLORS.primary : CHART_COLORS.danger} />
            </div>
            <div className="flex items-center gap-1 text-right">
              {c.change > 0 ? (
                <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
              ) : c.change < 0 ? (
                <TrendingDown className="h-3.5 w-3.5 text-red-500" />
              ) : (
                <Minus className="h-3.5 w-3.5 text-muted-foreground" />
              )}
              <span
                className={cn(
                  "text-xs font-semibold whitespace-nowrap",
                  c.change > 0
                    ? "text-emerald-500"
                    : c.change < 0
                    ? "text-red-500"
                    : "text-muted-foreground"
                )}
              >
                {formatPercent(c.change)}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
