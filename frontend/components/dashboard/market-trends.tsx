"use client";

import { motion } from "framer-motion";
import { TrendingUp, ArrowUpRight, ArrowDownRight, MapPin } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { cn, formatCurrency } from "@/lib/utils";
import type { DashboardData } from "@/lib/constants";

interface MarketTrendsProps {
  data: DashboardData["marketTrends"];
  className?: string;
}

const commodityColors: Record<string, string> = {
  Wheat: "#22c55e",
  Rice: "#3b82f6",
  Cotton: "#f59e0b",
};

export function MarketTrends({ data, className }: MarketTrendsProps) {
  const lineData = data.priceHistory.map((day) => {
    const row: Record<string, string | number> = { day: day.day };
    day.prices.forEach((p) => {
      row[p.commodity] = p.price;
    });
    return row;
  });

  const commodities = data.priceHistory[0]?.prices.map((p) => p.commodity) || [];

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-sm">Market Trends</h3>
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <MapPin className="h-3 w-3" />
          {data.marketName}
        </div>
      </div>

      <div className="h-[160px] w-full mb-3">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={lineData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
            <XAxis
              dataKey="day"
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${(v / 100).toFixed(0)}`}
            />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--popover))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
                fontSize: 12,
              }}
              formatter={(value: number) => [formatCurrency(value), ""]}
            />
            <Legend
              wrapperStyle={{ fontSize: 10, paddingTop: 4 }}
              iconType="circle"
              iconSize={8}
            />
            {commodities.map((commodity) => (
              <Line
                key={commodity}
                type="monotone"
                dataKey={commodity}
                stroke={commodityColors[commodity] || "#888"}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 3 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <p className="text-[10px] text-green-500 font-medium mb-1 flex items-center gap-1">
            <ArrowUpRight className="h-3 w-3" /> Top Gainers
          </p>
          {data.gainers.map((g) => (
            <div key={g.commodity} className="flex items-center justify-between text-xs py-0.5">
              <span className="text-muted-foreground">{g.commodity}</span>
              <span className="text-green-500 font-medium">+{g.change}%</span>
            </div>
          ))}
        </div>
        <div>
          <p className="text-[10px] text-red-500 font-medium mb-1 flex items-center gap-1">
            <ArrowDownRight className="h-3 w-3" /> Top Losers
          </p>
          {data.losers.map((l) => (
            <div key={l.commodity} className="flex items-center justify-between text-xs py-0.5">
              <span className="text-muted-foreground">{l.commodity}</span>
              <span className="text-red-500 font-medium">{l.change}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
