"use client";

import { motion } from "framer-motion";
import {
  Droplets,
  Wind,
  Eye,
  Thermometer,
  Sun,
  Gauge,
  Navigation,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface WeatherDetailsProps {
  rainProbability: number;
  windSpeed: number;
  windDirection: number;
  humidity: number;
  uvIndex: number;
  pressure: number;
  visibility: number;
}

function WindCompass({ degrees }: { degrees: number }) {
  const labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  const index = Math.round(degrees / 45) % 8;
  return (
    <div className="relative flex h-10 w-10 items-center justify-center rounded-full border border-border">
      <span className="text-[10px] font-medium text-muted-foreground">
        {labels[index]}
      </span>
      <div
        className="absolute left-1/2 top-1/2 h-4 w-0.5 -translate-x-1/2 origin-bottom rounded-full bg-primary transition-transform"
        style={{ transform: `translateX(-50%) rotate(${degrees}deg)` }}
      />
    </div>
  );
}

function UvBar({ value }: { value: number }) {
  const percent = Math.min((value / 11) * 100, 100);
  const color =
    value <= 2
      ? "bg-emerald-500"
      : value <= 5
        ? "bg-amber-500"
        : value <= 7
          ? "bg-orange-500"
          : value <= 10
            ? "bg-red-500"
            : "bg-violet-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="text-xs font-medium text-foreground w-6 text-right">
        {value}
      </span>
    </div>
  );
}

interface DetailCardProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  color: string;
  children?: React.ReactNode;
}

function DetailCard({ icon: Icon, label, value, color, children }: DetailCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-border/50 bg-muted/20 p-4 transition-colors hover:bg-muted/40"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg", color)}>
            <Icon className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="text-sm font-semibold text-foreground">{value}</p>
          </div>
        </div>
        {children}
      </div>
    </motion.div>
  );
}

export function WeatherDetails({
  rainProbability,
  windSpeed,
  windDirection,
  humidity,
  uvIndex,
  pressure,
  visibility,
}: WeatherDetailsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <div className="border-b border-border/50 px-5 py-4">
        <h3 className="text-sm font-semibold text-foreground">Weather Details</h3>
      </div>

      <div className="grid grid-cols-2 gap-3 p-5">
        <DetailCard
          icon={Droplets}
          label="Rain Probability"
          value={`${rainProbability}%`}
          color="bg-blue-500/10 text-blue-500"
        >
          <div className="h-8 w-8">
            <svg viewBox="0 0 36 36" className="h-full w-full">
              <path
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="hsl(var(--muted))"
                strokeWidth="4"
              />
              <path
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#3b82f6"
                strokeWidth="4"
                strokeDasharray={`${rainProbability}, 100`}
                className="transition-all"
              />
            </svg>
          </div>
        </DetailCard>

        <DetailCard
          icon={Wind}
          label="Wind Speed"
          value={`${windSpeed} km/h`}
          color="bg-cyan-500/10 text-cyan-500"
        >
          <WindCompass degrees={windDirection} />
        </DetailCard>

        <DetailCard
          icon={Droplets}
          label="Humidity"
          value={`${humidity}%`}
          color="bg-sky-500/10 text-sky-500"
        >
          <div className="h-8 w-12">
            <div className="flex h-full items-end gap-0.5">
              {[20, 40, 60, 80, 100].map((h) => (
                <div
                  key={h}
                  className={cn(
                    "flex-1 rounded-t-sm transition-all",
                    humidity >= h ? "bg-sky-500" : "bg-muted"
                  )}
                  style={{ height: `${h * 0.7}%` }}
                />
              ))}
            </div>
          </div>
        </DetailCard>

        <DetailCard
          icon={Sun}
          label="UV Index"
          value={uvIndex <= 2 ? "Low" : uvIndex <= 5 ? "Moderate" : uvIndex <= 7 ? "High" : uvIndex <= 10 ? "Very High" : "Extreme"}
          color="bg-amber-500/10 text-amber-500"
        >
          <div className="w-16">
            <UvBar value={uvIndex} />
          </div>
        </DetailCard>

        <DetailCard
          icon={Gauge}
          label="Pressure"
          value={`${pressure} hPa`}
          color="bg-purple-500/10 text-purple-500"
        />

        <DetailCard
          icon={Eye}
          label="Visibility"
          value={`${visibility} km`}
          color="bg-emerald-500/10 text-emerald-500"
        />
      </div>
    </motion.div>
  );
}
