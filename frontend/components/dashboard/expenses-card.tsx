"use client";

import { motion } from "framer-motion";
import { Wallet, TrendingDown, TrendingUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { cn, formatCurrency } from "@/lib/utils";
import type { DashboardData } from "@/lib/constants";

interface ExpensesCardProps {
  data: DashboardData["expenses"];
  className?: string;
}

export function ExpensesCard({ data, className }: ExpensesCardProps) {
  const isPositive = data.comparison >= 0;

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center gap-2 mb-3">
        <Wallet className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Expenses</h3>
      </div>

      <div className="flex items-baseline justify-between mb-1">
        <span className="text-2xl font-bold">{formatCurrency(data.total)}</span>
        <div className={cn(
          "flex items-center gap-1 text-sm font-medium",
          isPositive ? "text-red-500" : "text-green-500"
        )}>
          {isPositive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
          {isPositive ? "+" : ""}{data.comparison}%
        </div>
      </div>
      <p className="text-xs text-muted-foreground mb-3">vs last month</p>

      <div className="h-[160px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data.breakdown} margin={{ top: 5, right: 5, left: -20, bottom: 0 }} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`}
            />
            <YAxis
              type="category"
              dataKey="category"
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
              width={70}
            />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--popover))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
                fontSize: 12,
              }}
              formatter={(value: number) => [formatCurrency(value), "Amount"]}
            />
            <Bar dataKey="amount" radius={[0, 4, 4, 0]} barSize={16}>
              {data.breakdown.map((entry, i) => (
                <Cell key={entry.category} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
