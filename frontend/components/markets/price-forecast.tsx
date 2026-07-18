"use client";

import { motion } from "framer-motion";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Sparkles } from "lucide-react";
import { formatCurrency } from "@/lib/utils";
import { CHART_COLORS } from "@/lib/constants";
import type { ForecastPoint } from "@/lib/markets-data";

interface PriceForecastProps {
  data: ForecastPoint[];
}

export function PriceForecast({ data }: PriceForecastProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border bg-card p-4"
    >
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">Price Forecast</h3>
            <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-medium text-primary">
              <Sparkles className="h-3 w-3" />
              AI-Powered Forecast
            </span>
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">Next 7 days price prediction</p>
        </div>
      </div>

      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.2} />
                <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(v: number) => `${(v / 1000).toFixed(1)}K`}
              axisLine={false}
              tickLine={false}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "8px",
                fontSize: "13px",
              }}
              formatter={(value: number) => [formatCurrency(value), "Price"]}
              labelFormatter={(label: string) => `Date: ${label}`}
            />
            <Legend
              formatter={(value: string) => (
                <span className="text-xs text-foreground">{value}</span>
              )}
            />
            <Area
              type="monotone"
              dataKey="confidenceUpper"
              stroke="none"
              fill="url(#confidenceGradient)"
              name="Confidence Range"
            />
            <Area
              type="monotone"
              dataKey="confidenceLower"
              stroke="none"
              fill="url(#confidenceGradient)"
              name=""
            />
            <Line
              type="monotone"
              dataKey="actual"
              stroke={CHART_COLORS.primary}
              strokeWidth={2}
              name="Actual Price"
              dot={{ r: 3, strokeWidth: 0, fill: CHART_COLORS.primary }}
              connectNulls
              animationDuration={600}
            />
            <Line
              type="monotone"
              dataKey="predicted"
              stroke={CHART_COLORS.warning}
              strokeWidth={2}
              strokeDasharray="6 3"
              name="Predicted Price"
              dot={{ r: 3, strokeWidth: 0, fill: CHART_COLORS.warning }}
              animationDuration={600}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-3 border-t border-border pt-3">
        {[
          { label: "Current", value: data.find((d) => d.actual != null)?.actual ?? 0 },
          { label: "Forecast (7d)", value: data[data.length - 1]?.predicted ?? 0 },
          {
            label: "Trend",
            value: ((data[data.length - 1]?.predicted ?? 0) - (data.find((d) => d.actual != null)?.actual ?? 0)).toFixed(0),
            isUp: ((data[data.length - 1]?.predicted ?? 0) - (data.find((d) => d.actual != null)?.actual ?? 0)) >= 0,
          },
        ].map((item) => (
          <div key={item.label} className="text-center">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{item.label}</p>
            <p
              className={`mt-0.5 text-sm font-bold ${
                "isUp" in item
                  ? (item as { isUp: boolean }).isUp
                    ? "text-emerald-500"
                    : "text-red-500"
                  : "text-foreground"
              }`}
            >
              {item.label === "Trend" && ((item as { isUp: boolean }).isUp ? "+" : "")}
              {typeof item.value === "number"
                ? formatCurrency(item.value)
                : item.value}
            </p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
