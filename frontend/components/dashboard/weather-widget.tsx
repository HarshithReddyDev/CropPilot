"use client";

import { motion } from "framer-motion";
import { CloudSun, Droplets, Wind, MapPin, Sun, Cloud, CloudSunIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DashboardData } from "@/lib/constants";

interface WeatherWidgetProps {
  data: DashboardData["weather"];
  className?: string;
}

const weatherIcons: Record<string, typeof Sun> = {
  sun: Sun,
  "cloud-sun": CloudSunIcon,
  cloud: Cloud,
};

export function WeatherWidget({ data, className }: WeatherWidgetProps) {
  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center gap-2 mb-3">
        <CloudSun className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Today&apos;s Weather</h3>
      </div>

      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-bold">{data.temperature}°</span>
            <span className="text-sm text-muted-foreground">C</span>
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Feels like {data.feelsLike}°C
          </p>
        </div>
        <div className="flex flex-col items-end">
          <Sun className="h-10 w-10 text-amber-400" />
          <p className="text-xs text-muted-foreground mt-1 capitalize">
            {data.weatherMain}
          </p>
        </div>
      </div>

      <div className="flex gap-4 mb-4">
        <div className="flex items-center gap-1.5">
          <Droplets className="h-4 w-4 text-blue-400" />
          <span className="text-sm">{data.humidity}%</span>
        </div>
        <div className="flex items-center gap-1.5">
          <Wind className="h-4 w-4 text-cyan-400" />
          <span className="text-sm">{data.windSpeed} km/h</span>
        </div>
        <div className="flex items-center gap-1.5">
          <MapPin className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">{data.location}</span>
        </div>
      </div>

      <div className="border-t border-border pt-3">
        <p className="text-xs text-muted-foreground mb-2">6-Hour Forecast</p>
        <div className="flex justify-between">
          {data.hourlyForecast.map((hour, i) => {
            const Icon = weatherIcons[hour.icon] || Cloud;
            return (
              <motion.div
                key={hour.time}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.06, duration: 0.25 }}
                className="flex flex-col items-center gap-1"
              >
                <span className="text-[10px] text-muted-foreground">{hour.time}</span>
                <Icon className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium">{hour.temp}°</span>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
