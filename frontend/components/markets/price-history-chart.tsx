"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CHART_COLORS } from "@/lib/constants";
import { formatCurrency } from "@/lib/utils";
import { useTranslation, formatNumber } from "@/lib/i18n";
import type { MarketHistoryPoint } from "@/types";

function shortDate(iso: string): string {
  return iso.length >= 10 ? iso.slice(5, 10) : iso;
}

export function PriceHistoryChart({ points }: { points: MarketHistoryPoint[] }) {
  const { t, locale } = useTranslation();
  if (points.length === 0) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 text-center">
        <p className="text-sm font-medium text-foreground">{t("markets.histNoData")}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          {t("markets.histNoDataBody")}
        </p>
      </div>
    );
  }

  const head = points[0];
  const subtitleParts = [head.market, head.variety, head.grade].filter(
    (p) => p && p.trim() !== ""
  );

  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            {t("markets.histTitle")}
          </h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {subtitleParts.join(" · ")} · {t("markets.histUnit", { unit: head.price_per_unit.replace("INR/", "") })}
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          {t("markets.histCount", { count: points.length })}
        </p>
      </div>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={points} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="modal-gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.3} />
                <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
            <XAxis
              dataKey="arrival_date"
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={shortDate}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              tickFormatter={(v: number) => `Rs${(v / 1000).toFixed(1)}K`}
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
              labelFormatter={(label: string) => t("markets.histObserved", { label })}
              formatter={(value: number, name: string) => [formatCurrency(value), name]}
            />
            <Area
              type="monotone"
              dataKey="modal_price"
              name={t("markets.histModal")}
              stroke={CHART_COLORS.primary}
              strokeWidth={2}
              fill="url(#modal-gradient)"
              dot={false}
              activeDot={{ r: 4, strokeWidth: 0 }}
            />
            <Line
              type="monotone"
              dataKey="max_price"
              name={t("markets.histMax")}
              stroke={CHART_COLORS.warning}
              strokeWidth={1}
              strokeDasharray="4 3"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="min_price"
              name={t("markets.histMin")}
              stroke={CHART_COLORS.secondary}
              strokeWidth={1}
              strokeDasharray="4 3"
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
