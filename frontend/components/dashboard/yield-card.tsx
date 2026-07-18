"use client";

import { motion } from "framer-motion";
import { Wheat, Target } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { cn } from "@/lib/utils";
import type { DashboardData } from "@/lib/constants";

interface YieldCardProps {
  data: DashboardData["yield"];
  className?: string;
}

export function YieldCard({ data, className }: YieldCardProps) {
  const barData = data.cropWise.map((c) => ({
    name: c.crop,
    Current: c.yield,
    Target: c.target,
  }));

  const targetPercent = Math.round((data.total / data.target) * 100);

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center gap-2 mb-3">
        <Wheat className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Yield</h3>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <p className="text-xs text-muted-foreground">Total Yield</p>
          <p className="text-xl font-bold">{data.total} q</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Per Hectare</p>
          <p className="text-xl font-bold">{data.perHectare} q/ha</p>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <Target className="h-4 w-4 text-muted-foreground" />
        <div className="flex items-center gap-1.5 flex-1">
          <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-primary"
              initial={{ width: 0 }}
              animate={{ width: `${targetPercent}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </div>
          <span className="text-xs text-muted-foreground">{targetPercent}% of target</span>
        </div>
      </div>

      <div className="h-[140px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={barData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
            <XAxis
              dataKey="name"
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--popover))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "var(--radius)",
                fontSize: 12,
              }}
            />
            <Bar dataKey="Current" radius={[4, 4, 0, 0]} barSize={14} fill="hsl(var(--chart-1))" />
            <Bar dataKey="Target" radius={[4, 4, 0, 0]} barSize={14} fill="hsl(var(--muted-foreground))" fillOpacity={0.3} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
