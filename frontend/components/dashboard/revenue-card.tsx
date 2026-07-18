"use client";

import { motion } from "framer-motion";
import { IndianRupee, TrendingUp, TrendingDown } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { cn, formatCurrency } from "@/lib/utils";
import type { DashboardData } from "@/lib/constants";

interface RevenueCardProps {
  data: DashboardData["revenue"];
  className?: string;
}

export function RevenueCard({ data, className }: RevenueCardProps) {
  const isPositive = data.comparison >= 0;

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center gap-2 mb-3">
        <IndianRupee className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Revenue</h3>
      </div>

      <div className="flex items-baseline justify-between mb-1">
        <span className="text-2xl font-bold">{formatCurrency(data.total)}</span>
        <div className={cn(
          "flex items-center gap-1 text-sm font-medium",
          isPositive ? "text-green-500" : "text-red-500"
        )}>
          {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
          {isPositive ? "+" : ""}{data.comparison}%
        </div>
      </div>
      <p className="text-xs text-muted-foreground mb-3">vs last month</p>

      <div className="h-[140px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data.monthly} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-3))" stopOpacity={0.3} />
                <stop offset="95%" stopColor="hsl(var(--chart-3))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
            />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--popover))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
                fontSize: 12,
              }}
              formatter={(value: number) => [formatCurrency(value), "Revenue"]}
            />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="hsl(var(--chart-3))"
              strokeWidth={2}
              fill="url(#revenueGradient)"
              dot={false}
              activeDot={{ r: 4, fill: "hsl(var(--chart-3))" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
