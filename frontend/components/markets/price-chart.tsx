"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { cn, formatCurrency } from "@/lib/utils";
import { CHART_COLORS } from "@/lib/constants";
import type { PriceHistoryPoint } from "@/lib/markets-data";

interface PriceChartProps {
  data: PriceHistoryPoint[];
}

const ranges = [
  { label: "7D", days: 7 },
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "1Y", days: 365 },
] as const;

const commodities = ["Rice", "Wheat", "Maize", "Cotton"];

export function PriceChart({ data }: PriceChartProps) {
  const [range, setRange] = useState<(typeof ranges)[number]["label"]>("1M");
  const [selectedCommodities, setSelectedCommodities] = useState<Set<string>>(
    new Set(commodities.slice(0, 2))
  );

  const days = ranges.find((r) => r.label === range)?.days ?? 30;

  const chartData = useMemo(() => {
    const grouped: Record<string, { date: string; values: Record<string, number> }> = {};
    for (const point of data) {
      if (!grouped[point.date]) grouped[point.date] = { date: point.date, values: {} };
      grouped[point.date].values[point.commodity] = point.price;
    }
    let entries = Object.values(grouped);
    if (days < 365) entries = entries.slice(-days);
    return entries;
  }, [data, days]);

  const colors = [CHART_COLORS.primary, CHART_COLORS.secondary, CHART_COLORS.warning, CHART_COLORS.purple];

  const toggleCommodity = (c: string) => {
    const next = new Set(selectedCommodities);
    if (next.has(c) && next.size > 1) next.delete(c);
    else next.add(c);
    setSelectedCommodities(next);
  };

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          {commodities.map((c, i) => (
            <button
              key={c}
              onClick={() => toggleCommodity(c)}
              className={cn(
                "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors",
                selectedCommodities.has(c)
                  ? "bg-primary/10 text-primary"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              )}
            >
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: colors[i] }} />
              {c}
            </button>
          ))}
        </div>
        <div className="flex gap-1 rounded-lg bg-muted p-0.5">
          {ranges.map((r) => (
            <button
              key={r.label}
              onClick={() => setRange(r.label)}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                range === r.label
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
            <defs>
              {commodities.map((c, i) => (
                <linearGradient key={c} id={`gradient-${c}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={colors[i]} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={colors[i]} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(v: string) => v.slice(5)}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(v: number) => `₹${(v / 1000).toFixed(1)}K`}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                fontSize: "13px",
              }}
              formatter={(value: number, name: string) => [formatCurrency(value), name]}
            />
            <Legend
              formatter={(value: string) => (
                <span className="text-xs text-foreground">{value}</span>
              )}
            />
            {commodities.map((c, i) =>
              selectedCommodities.has(c) ? (
                <Area
                  key={c}
                  type="monotone"
                  dataKey={`values.${c}`}
                  name={c}
                  stroke={colors[i]}
                  strokeWidth={2}
                  fill={`url(#gradient-${c})`}
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 0 }}
                  animationDuration={600}
                />
              ) : null
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
