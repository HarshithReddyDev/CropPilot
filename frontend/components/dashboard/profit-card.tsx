"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { AreaChart, Area, ResponsiveContainer } from "recharts";
import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import type { DashboardData } from "@/lib/constants";

interface ProfitCardProps {
  data: DashboardData["profit"];
  className?: string;
}

export function ProfitCard({ data, className }: ProfitCardProps) {
  const isUp = data.trendDirection === "up";
  const chartData = data.trend.map((v, i) => ({ index: i, value: v }));

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Net Profit</h3>
      </div>

      <div className="flex items-baseline justify-between mb-1">
        <span className="text-2xl font-bold">{formatCurrency(data.netProfit)}</span>
        <div className={cn(
          "flex items-center gap-1 text-sm font-medium",
          isUp ? "text-green-500" : "text-red-500"
        )}>
          {isUp ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
          {formatPercent(data.margin - 50)}
        </div>
      </div>

      <div className="flex gap-3 mb-3">
        <div className="flex items-center gap-1">
          <span className="text-xs text-muted-foreground">Margin:</span>
          <span className="text-sm font-semibold">{data.margin.toFixed(1)}%</span>
        </div>
        {isUp ? (
          <TrendingUp className="h-4 w-4 text-green-500" />
        ) : (
          <TrendingDown className="h-4 w-4 text-red-500" />
        )}
      </div>

      <div className="h-[60px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={isUp ? "#22c55e" : "#ef4444"} stopOpacity={0.3} />
                <stop offset="100%" stopColor={isUp ? "#22c55e" : "#ef4444"} stopOpacity={0} />
              </linearGradient>
            </defs>
            <Area
              type="monotone"
              dataKey="value"
              stroke={isUp ? "#22c55e" : "#ef4444"}
              strokeWidth={2}
              fill="url(#profitGradient)"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
