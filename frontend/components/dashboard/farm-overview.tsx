"use client";

import { motion } from "framer-motion";
import { Tractor, MapPin, LayoutGrid, CalendarDays } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DashboardData } from "@/lib/constants";

interface FarmOverviewProps {
  data: DashboardData["farmOverview"];
  className?: string;
}

export function FarmOverview({ data, className }: FarmOverviewProps) {
  const stats = [
    {
      label: "Total Farms",
      value: data.totalFarms,
      icon: Tractor,
      color: "text-green-500",
      bg: "bg-green-500/10",
    },
    {
      label: "Total Area",
      value: `${data.totalAreaHectares} ha`,
      icon: MapPin,
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      label: "Active Plots",
      value: data.activePlots,
      icon: LayoutGrid,
      color: "text-amber-500",
      bg: "bg-amber-500/10",
    },
    {
      label: "Current Season",
      value: data.currentSeason,
      icon: CalendarDays,
      color: "text-purple-500",
      bg: "bg-purple-500/10",
    },
  ];

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center gap-2 mb-4">
        <Tractor className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Farm Overview</h3>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.3 }}
            className={cn(
              "flex items-center gap-3 rounded-xl p-3",
              stat.bg
            )}
          >
            <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", stat.bg)}>
              <stat.icon className={cn("h-5 w-5", stat.color)} />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-lg font-bold">{stat.value}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
