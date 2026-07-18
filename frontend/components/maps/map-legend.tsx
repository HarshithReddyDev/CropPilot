"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import type { LayerVisibility } from "@/app/maps/page";

interface LegendLayer {
  key: keyof LayerVisibility;
  label: string;
  color: string;
}

interface MapLegendProps {
  layers: LegendLayer[];
  visibility: LayerVisibility;
}

export function MapLegend({ layers, visibility }: MapLegendProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.3 }}
      className={cn(
        "absolute bottom-6 right-6 z-10",
        "backdrop-blur-xl bg-background/80 border border-border/50 rounded-2xl shadow-2xl",
        "max-w-[200px]"
      )}
    >
      <div className="p-3">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-between w-full mb-1"
        >
          <span className="text-xs font-semibold text-foreground/80 uppercase tracking-wider">
            Legend
          </span>
          <svg
            className={cn(
              "h-3.5 w-3.5 text-muted-foreground transition-transform",
              collapsed && "rotate-180"
            )}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </button>

        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="space-y-2 pt-1"
            >
              {layers.map(({ key, label, color }) => (
                <div
                  key={key}
                  className={cn(
                    "flex items-center gap-2.5 transition-opacity",
                    !visibility[key] && "opacity-40"
                  )}
                >
                  <div className="flex items-center gap-1.5">
                    <div
                      className="w-3 h-3 rounded-sm"
                      style={{ backgroundColor: color }}
                    />
                    {key === "diseaseHeatmap" && (
                      <div className="flex gap-0.5">
                        <div className="w-2 h-3 rounded-sm" style={{ backgroundColor: "#3b82f6" }} />
                        <div className="w-2 h-3 rounded-sm" style={{ backgroundColor: "#f59e0b" }} />
                        <div className="w-2 h-3 rounded-sm" style={{ backgroundColor: "#ef4444" }} />
                      </div>
                    )}
                  </div>
                  <span className="text-[11px] font-medium text-foreground/70">
                    {label}
                  </span>
                </div>
              ))}

              {visibility.diseaseHeatmap && (
                <div className="pt-1.5 border-t border-border/30">
                  <div className="flex items-center gap-1 justify-between px-0.5">
                    <span className="text-[9px] text-muted-foreground">Low</span>
                    <div className="flex-1 h-2 rounded-full mx-1 overflow-hidden flex">
                      <div className="flex-1" style={{ backgroundColor: "#3b82f6" }} />
                      <div className="flex-1" style={{ backgroundColor: "#f59e0b" }} />
                      <div className="flex-1" style={{ backgroundColor: "#ef4444" }} />
                    </div>
                    <span className="text-[9px] text-muted-foreground">High</span>
                  </div>
                  <p className="text-[9px] text-center text-muted-foreground mt-0.5">Disease Confidence</p>
                </div>
              )}

              {visibility.weather && (
                <div className="pt-1.5 border-t border-border/30">
                  <div className="flex items-center gap-1 justify-between px-0.5">
                    <span className="text-[9px] text-muted-foreground">Cool</span>
                    <div className="flex-1 h-2 rounded-full mx-1 overflow-hidden flex">
                      <div className="flex-1" style={{ backgroundColor: "#3b82f6" }} />
                      <div className="flex-1" style={{ backgroundColor: "#fbbf24" }} />
                      <div className="flex-1" style={{ backgroundColor: "#ef4444" }} />
                    </div>
                    <span className="text-[9px] text-muted-foreground">Hot</span>
                  </div>
                  <p className="text-[9px] text-center text-muted-foreground mt-0.5">Temperature</p>
                </div>
              )}

              {visibility.markets && (
                <div className="pt-1.5 border-t border-border/30 space-y-1">
                  {[
                    { label: "High Price (>₹3000)", color: "#ef4444" },
                    { label: "Medium Price (₹2900-3000)", color: "#f59e0b" },
                    { label: "Low Price (<₹2900)", color: "#22c55e" },
                  ].map(({ label, color }) => (
                    <div key={label} className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                      <span className="text-[10px] text-muted-foreground">{label}</span>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
