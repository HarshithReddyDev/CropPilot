"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Layers,
  Satellite,
  Map as MapIcon,
  Bug,
  CloudSun,
  TrendingUp,
  Radio,
  Crosshair,
  ZoomIn,
  ZoomOut,
  Home,
} from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { LayerVisibility } from "@/app/maps/page";

const layerConfig = [
  { key: "satellite" as const, label: "Satellite", icon: Satellite, color: "#3b82f6" },
  { key: "farmBoundaries" as const, label: "Farm Boundaries", icon: MapIcon, color: "#22c55e" },
  { key: "diseaseHeatmap" as const, label: "Disease Heatmap", icon: Bug, color: "#ef4444" },
  { key: "weather" as const, label: "Weather", icon: CloudSun, color: "#06b6d4" },
  { key: "markets" as const, label: "Markets", icon: TrendingUp, color: "#f59e0b" },
  { key: "drone" as const, label: "Drone", icon: Radio, color: "#8b5cf6" },
];

interface MapControlsProps {
  layers: LayerVisibility;
  onToggle: (key: keyof LayerVisibility) => void;
}

export function MapControls({ layers, onToggle }: MapControlsProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
      className={cn(
        "absolute bottom-6 left-6 z-10",
        "backdrop-blur-xl bg-background/80 border border-border/50 rounded-2xl shadow-2xl",
        "transition-all duration-300"
      )}
    >
      <div className="p-3 space-y-3">
        <div className="flex items-center justify-between gap-3">
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-xs font-semibold text-foreground/80 uppercase tracking-wider"
            >
              Layers
            </motion.span>
          )}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1.5 rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          >
            <Layers className="h-4 w-4" />
          </button>
        </div>

        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-1.5"
          >
            {layerConfig.map(({ key, label, icon: Icon, color }) => (
              <div
                key={key}
                className="flex items-center justify-between gap-3 px-2 py-1.5 rounded-lg hover:bg-accent/50 transition-colors group"
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: color, opacity: layers[key] ? 1 : 0.3 }}
                  />
                  <Icon className={cn(
                    "h-3.5 w-3.5 transition-colors",
                    layers[key] ? "text-foreground" : "text-muted-foreground"
                  )} />
                  <span className={cn(
                    "text-xs font-medium transition-colors",
                    layers[key] ? "text-foreground" : "text-muted-foreground"
                  )}>
                    {label}
                  </span>
                </div>
                <Switch
                  checked={layers[key]}
                  onCheckedChange={() => onToggle(key)}
                  className="scale-75 data-[state=checked]:bg-primary"
                />
              </div>
            ))}

            <div className="h-px bg-border/50 my-2" />

            <div className="grid grid-cols-3 gap-1.5">
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1">
                <Crosshair className="h-3 w-3" />
                Reset
              </Button>
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1">
                <Home className="h-3 w-3" />
                My Farms
              </Button>
              <div className="flex gap-1.5">
                <Button variant="outline" size="icon" className="h-8 w-8">
                  <ZoomIn className="h-3.5 w-3.5" />
                </Button>
                <Button variant="outline" size="icon" className="h-8 w-8">
                  <ZoomOut className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
