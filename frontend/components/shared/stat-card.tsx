"use client";

import { type LucideIcon, TrendingUp, TrendingDown } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface StatCardProps {
  icon: LucideIcon;
  label: string;
  value: string | number;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  sparkline?: number[];
  className?: string;
}

export function StatCard({
  icon: Icon,
  label,
  value,
  trend,
  sparkline,
  className,
}: StatCardProps) {
  const maxSpark = sparkline ? Math.max(...sparkline) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "group relative overflow-hidden rounded-xl border border-border bg-card p-5 transition-shadow hover:shadow-lg",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold tracking-tight text-foreground">
              {value}
            </p>
          </div>
        </div>
        {trend && (
          <div
            className={cn(
              "flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
              trend.isPositive
                ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400"
                : "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400"
            )}
          >
            {trend.isPositive ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {Math.abs(trend.value)}%
          </div>
        )}
      </div>
      {sparkline && sparkline.length > 0 && (
        <div className="mt-4 h-10">
          <svg
            viewBox={`0 0 ${sparkline.length - 1} 100`}
            className="h-full w-full"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
              </linearGradient>
            </defs>
            <path
              d={sparkline
                .map(
                  (v, i) =>
                    `${i === 0 ? "M" : "L"}${i} ${100 - (v / maxSpark) * 90}`
                )
                .join(" ")}
              fill="none"
              stroke="hsl(var(--primary))"
              strokeWidth="2"
              vectorEffect="non-scaling-stroke"
            />
            <path
              d={`${sparkline
                .map(
                  (v, i) =>
                    `${i === 0 ? "M" : "L"}${i} ${100 - (v / maxSpark) * 90}`
                )
                .join(" ")} L${sparkline.length - 1} 100 L0 100 Z`}
              fill="url(#sparkGrad)"
            />
          </svg>
        </div>
      )}
    </motion.div>
  );
}
