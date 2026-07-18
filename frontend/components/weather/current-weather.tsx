"use client";

import { motion } from "framer-motion";
import {
  Sun,
  Cloud,
  CloudRain,
  CloudSnow,
  CloudFog,
  CloudLightning,
  Moon,
  Thermometer,
  ArrowUp,
  ArrowDown,
  Droplets,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface CurrentWeatherProps {
  location: string;
  date: string;
  temperature: number;
  feelsLike: number;
  high: number;
  low: number;
  description: string;
  humidity: number;
  condition: "sunny" | "cloudy" | "rainy" | "snowy" | "foggy" | "stormy" | "clear-night";
}

const conditionConfig = {
  sunny: {
    icon: Sun,
    gradient: "from-amber-400 via-orange-400 to-yellow-300",
    darkGradient: "from-amber-500/20 via-orange-500/10 to-transparent",
    textColor: "text-amber-100",
    tempColor: "text-white",
  },
  "clear-night": {
    icon: Moon,
    gradient: "from-indigo-800 via-blue-900 to-slate-900",
    darkGradient: "from-indigo-500/20 via-blue-500/10 to-transparent",
    textColor: "text-blue-100",
    tempColor: "text-white",
  },
  cloudy: {
    icon: Cloud,
    gradient: "from-slate-400 via-slate-500 to-gray-600",
    darkGradient: "from-slate-500/20 via-slate-400/10 to-transparent",
    textColor: "text-slate-100",
    tempColor: "text-white",
  },
  rainy: {
    icon: CloudRain,
    gradient: "from-blue-600 via-blue-700 to-slate-800",
    darkGradient: "from-blue-500/20 via-blue-600/10 to-transparent",
    textColor: "text-blue-100",
    tempColor: "text-white",
  },
  snowy: {
    icon: CloudSnow,
    gradient: "from-blue-200 via-slate-100 to-white",
    darkGradient: "from-blue-300/20 via-slate-200/10 to-transparent",
    textColor: "text-slate-800",
    tempColor: "text-slate-900",
  },
  foggy: {
    icon: CloudFog,
    gradient: "from-gray-400 via-gray-500 to-gray-600",
    darkGradient: "from-gray-500/20 via-gray-400/10 to-transparent",
    textColor: "text-gray-100",
    tempColor: "text-white",
  },
  stormy: {
    icon: CloudLightning,
    gradient: "from-gray-700 via-gray-800 to-slate-900",
    darkGradient: "from-gray-600/20 via-gray-700/10 to-transparent",
    textColor: "text-gray-100",
    tempColor: "text-white",
  },
};

export function CurrentWeather({
  location,
  date,
  temperature,
  feelsLike,
  high,
  low,
  description,
  humidity,
  condition,
}: CurrentWeatherProps) {
  const config = conditionConfig[condition];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "relative overflow-hidden rounded-2xl border border-white/10",
        "bg-gradient-to-br",
        config.gradient
      )}
    >
      <div className={cn("absolute inset-0 bg-gradient-to-t", config.darkGradient)} />

      <div className="relative p-6 sm:p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-1">
            <motion.h2
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className={cn("text-xl font-bold sm:text-2xl", config.textColor)}
            >
              {location}
            </motion.h2>
            <p className={cn("text-sm opacity-80", config.textColor)}>{date}</p>
            <p className={cn("mt-1 text-sm font-medium capitalize", config.textColor)}>
              {description}
            </p>
          </div>

          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ type: "spring", stiffness: 200 }}
            className="flex items-center gap-4"
          >
            <Icon
              className={cn(
                "h-14 w-14 sm:h-20 sm:w-20",
                condition === "sunny" && "animate-[spin_20s_linear_infinite]",
                condition === "rainy" && "animate-bounce"
              )}
              style={{
                filter:
                  condition === "sunny"
                    ? "drop-shadow(0 0 20px rgba(251, 191, 36, 0.5))"
                    : undefined,
              }}
            />
            <div className="text-right">
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className={cn(
                  "text-5xl font-extrabold tracking-tight sm:text-6xl",
                  config.tempColor
                )}
              >
                {Math.round(temperature)}°
              </motion.p>
              <p className={cn("text-sm opacity-80", config.textColor)}>
                <Thermometer className="mr-1 inline h-3.5 w-3.5" />
                Feels like {Math.round(feelsLike)}°
              </p>
            </div>
          </motion.div>
        </div>

        <div className="mt-6 grid grid-cols-3 gap-4 rounded-xl bg-white/10 p-4 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <ArrowUp className={cn("h-4 w-4", config.textColor)} />
            <span className={cn("text-sm", config.textColor)}>
              H: {Math.round(high)}°
            </span>
          </div>
          <div className="flex items-center gap-2">
            <ArrowDown className={cn("h-4 w-4", config.textColor)} />
            <span className={cn("text-sm", config.textColor)}>
              L: {Math.round(low)}°
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Droplets className={cn("h-4 w-4", config.textColor)} />
            <span className={cn("text-sm", config.textColor)}>{humidity}%</span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
