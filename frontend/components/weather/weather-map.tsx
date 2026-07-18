"use client";

import { motion } from "framer-motion";
import { MapPin, Navigation, CloudRain, Thermometer, ExternalLink } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface TemperatureMarker {
  lat: number;
  lng: number;
  temp: number;
  label: string;
}

interface WeatherMapProps {
  center: { lat: number; lng: number };
  temperatures?: TemperatureMarker[];
  locationName?: string;
}

export function WeatherMap({
  center,
  temperatures,
  locationName,
}: WeatherMapProps) {
  const defaultTemps: TemperatureMarker[] = temperatures ?? [
    { lat: 0.15, lng: 0.2, temp: 34, label: "Field A" },
    { lat: 0.65, lng: 0.25, temp: 32, label: "Field B" },
    { lat: 0.35, lng: 0.7, temp: 33, label: "Field C" },
    { lat: 0.75, lng: 0.75, temp: 31, label: "Field D" },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <div className="flex items-center justify-between border-b border-border/50 px-5 py-4">
        <div className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-semibold text-foreground">Weather Map</h3>
        </div>
        <Link
          href="/maps"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-primary transition-colors hover:text-primary/80"
        >
          View Full Map
          <ExternalLink className="h-3.5 w-3.5" />
        </Link>
      </div>

      <div className="relative h-56 bg-gradient-to-br from-muted to-muted/50 sm:h-64">
        <div className="absolute inset-0 opacity-[0.03] dark:opacity-[0.08]">
          <svg className="h-full w-full" viewBox="0 0 400 200">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>

        <div className="absolute inset-4 rounded-lg border border-border/30 bg-muted/20 backdrop-blur-[2px]">
          <div className="flex h-full items-center justify-center">
            <div className="relative h-full w-full">
              <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
                <div className="flex flex-col items-center gap-2">
                  <div className="relative">
                    <MapPin className="h-8 w-8 text-primary" />
                    <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-primary px-2 py-0.5 text-[10px] font-medium text-primary-foreground">
                      {locationName ?? "Your Location"}
                    </span>
                  </div>
                </div>
              </div>

              {defaultTemps.map((t, i) => (
                <div
                  key={i}
                  className="absolute flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 backdrop-blur-sm"
                  style={{ left: `${t.lng * 80 + 10}%`, top: `${t.lat * 70 + 15}%` }}
                >
                  <Thermometer className="h-3 w-3 text-amber-500" />
                  <span className="text-[10px] font-semibold text-amber-500">
                    {t.temp}°
                  </span>
                  <span className="text-[8px] text-muted-foreground">{t.label}</span>
                </div>
              ))}

              <div className="absolute bottom-3 right-3 flex items-center gap-2 rounded-lg bg-background/80 px-3 py-1.5 backdrop-blur-sm">
                <CloudRain className="h-3.5 w-3.5 text-blue-500" />
                <span className="text-[10px] font-medium text-foreground">Rain Radar</span>
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
                </span>
              </div>

              <div className="absolute bottom-3 left-3">
                <Navigation className="h-4 w-4 text-muted-foreground" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
