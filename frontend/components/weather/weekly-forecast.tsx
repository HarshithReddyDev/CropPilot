"use client";

import { motion } from "framer-motion";
import {
  Sun,
  Cloud,
  CloudRain,
  CloudSnow,
  CloudLightning,
  CloudFog,
  Moon,
  Droplets,
  Wind,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface DayForecast {
  day: string;
  date: string;
  high: number;
  low: number;
  condition: string;
  rainProbability: number;
  windSpeed: number;
  isToday?: boolean;
}

interface WeeklyForecastProps {
  data: DayForecast[];
}

const conditionIcon = (condition: string) => {
  const c = condition.toLowerCase();
  if (c.includes("rain") || c.includes("drizzle")) return CloudRain;
  if (c.includes("snow") || c.includes("ice")) return CloudSnow;
  if (c.includes("thunder") || c.includes("storm")) return CloudLightning;
  if (c.includes("fog") || c.includes("mist") || c.includes("haze")) return CloudFog;
  if (c.includes("cloud") || c.includes("overcast")) return Cloud;
  if (c.includes("clear") || c.includes("sunny")) return Sun;
  return Cloud;
};

export function WeeklyForecast({ data }: WeeklyForecastProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <div className="flex items-center gap-2 border-b border-border/50 px-5 py-4">
        <Sun className="h-5 w-5 text-primary" />
        <h3 className="text-sm font-semibold text-foreground">7-Day Forecast</h3>
      </div>

      <div className="divide-y divide-border/30">
        {data.map((day, i) => {
          const Icon = conditionIcon(day.condition);
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className={cn(
                "grid grid-cols-5 items-center gap-4 px-5 py-3.5 transition-colors hover:bg-muted/30",
                day.isToday && "bg-primary/5"
              )}
            >
              <div className="flex items-center gap-3">
                <p
                  className={cn(
                    "text-sm font-medium min-w-[3rem]",
                    day.isToday ? "text-primary" : "text-foreground"
                  )}
                >
                  {day.day}
                </p>
                <p className="hidden text-[10px] text-muted-foreground sm:block">
                  {day.date}
                </p>
              </div>

              <div className="flex items-center justify-center">
                <Icon
                  className={cn(
                    "h-5 w-5",
                    day.isToday ? "text-primary" : "text-muted-foreground"
                  )}
                />
              </div>

              <div className="flex items-center justify-center gap-2">
                <span className="text-sm font-semibold text-foreground">
                  {Math.round(day.high)}°
                </span>
                <span className="text-sm text-muted-foreground">
                  {Math.round(day.low)}°
                </span>
              </div>

              <div className="flex items-center justify-center gap-1.5">
                <Droplets className="h-3.5 w-3.5 text-blue-500" />
                <span className="text-xs text-muted-foreground">
                  {day.rainProbability}%
                </span>
              </div>

              <div className="flex items-center justify-end gap-1.5">
                <Wind className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  {day.windSpeed} km/h
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
