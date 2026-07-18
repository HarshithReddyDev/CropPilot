"use client";

import { useRef } from "react";
import { motion } from "framer-motion";
import {
  CloudSun,
  CloudRain,
  Cloud,
  Sun,
  Moon,
  Snowflake,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface HourlyData {
  time: string;
  temp: number;
  condition: string;
  rainProbability: number;
  isCurrent?: boolean;
}

interface HourlyForecastProps {
  data: HourlyData[];
}

const conditionIcon = (condition: string) => {
  const c = condition.toLowerCase();
  if (c.includes("rain") || c.includes("drizzle")) return CloudRain;
  if (c.includes("snow") || c.includes("ice")) return Snowflake;
  if (c.includes("cloud") || c.includes("overcast")) return Cloud;
  if (c.includes("clear") || c.includes("sunny")) {
    const hour = new Date().getHours();
    return hour >= 6 && hour < 18 ? Sun : Moon;
  }
  return CloudSun;
};

export function HourlyForecast({ data }: HourlyForecastProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const amount = 280;
      scrollRef.current.scrollBy({
        left: direction === "left" ? -amount : amount,
        behavior: "smooth",
      });
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <div className="flex items-center justify-between border-b border-border/50 px-5 py-4">
        <div className="flex items-center gap-2">
          <CloudSun className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">Hourly Forecast</h3>
        </div>
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => scroll("left")}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => scroll("right")}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex gap-3 overflow-x-auto px-5 py-4 scrollbar-hide"
      >
        {data.map((hour, i) => {
          const Icon = conditionIcon(hour.condition);
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              className={cn(
                "flex shrink-0 flex-col items-center gap-2 rounded-xl px-4 py-3 transition-all",
                hour.isCurrent
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20"
                  : "bg-muted/50 text-foreground hover:bg-muted"
              )}
            >
              <span
                className={cn(
                  "text-xs font-medium",
                  hour.isCurrent ? "text-primary-foreground/80" : "text-muted-foreground"
                )}
              >
                {hour.time}
              </span>
              <Icon
                className={cn(
                  "h-6 w-6",
                  hour.isCurrent ? "text-primary-foreground" : "text-primary"
                )}
              />
              <span className="text-sm font-bold">{Math.round(hour.temp)}°</span>
              {hour.rainProbability > 0 && (
                <span
                  className={cn(
                    "flex items-center gap-1 text-[10px]",
                    hour.isCurrent
                      ? "text-primary-foreground/70"
                      : "text-blue-500"
                  )}
                >
                  <CloudRain className="h-3 w-3" />
                  {hour.rainProbability}%
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
