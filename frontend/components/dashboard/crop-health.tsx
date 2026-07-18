"use client";

import { motion } from "framer-motion";
import { Sprout, TrendingUp, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Progress } from "@/components/ui/progress";
import type { DashboardData } from "@/lib/constants";

interface CropHealthProps {
  data: DashboardData["cropHealth"];
  className?: string;
}

export function CropHealth({ data, className }: CropHealthProps) {
  const circumference = 2 * Math.PI * 44;
  const offset = circumference - (data.overallScore / 100) * circumference;

  const healthColor =
    data.overallScore >= 80
      ? "stroke-green-500"
      : data.overallScore >= 60
        ? "stroke-amber-500"
        : "stroke-red-500";

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center gap-2 mb-4">
        <Sprout className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Crop Health</h3>
      </div>

      <div className="flex items-center gap-5 mb-4">
        <div className="relative flex items-center justify-center">
          <svg width="100" height="100" className="-rotate-90">
            <circle
              cx="50"
              cy="50"
              r="44"
              fill="none"
              stroke="hsl(var(--muted))"
              strokeWidth="6"
            />
            <motion.circle
              cx="50"
              cy="50"
              r="44"
              fill="none"
              strokeWidth="6"
              strokeLinecap="round"
              className={healthColor}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: offset }}
              transition={{ duration: 1.2, ease: "easeOut" }}
              strokeDasharray={circumference}
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            <span className="text-xl font-bold">{data.overallScore}%</span>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {data.trend >= 0 ? (
            <TrendingUp className="h-4 w-4 text-green-500" />
          ) : (
            <TrendingDown className="h-4 w-4 text-red-500" />
          )}
          <span className={cn("text-sm font-medium", data.trend >= 0 ? "text-green-500" : "text-red-500")}>
            {data.trend >= 0 ? "+" : ""}{data.trend}%
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {data.crops.map((crop, i) => (
          <motion.div
            key={crop.crop}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1, duration: 0.3 }}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm">{crop.crop}</span>
              <span className="text-sm font-medium">{crop.health}%</span>
            </div>
            <Progress value={crop.health} className="h-2" />
          </motion.div>
        ))}
      </div>
    </div>
  );
}
