"use client";

import { motion } from "framer-motion";
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Thermometer,
  ShoppingCart,
  Calendar,
  Truck,
  Warehouse,
} from "lucide-react";
import { cn, formatCurrency } from "@/lib/utils";
import type { AIRecommendation } from "@/lib/markets-data";

interface AIRecommendationCardProps {
  data: AIRecommendation;
}

const factorIcons: Record<string, typeof Thermometer> = {
  "Weather conditions": Thermometer,
  "Market demand": ShoppingCart,
  "Seasonal trend": Calendar,
  "Transportation costs": Truck,
  "Storage availability": Warehouse,
};

export function AIRecommendationCard({ data }: AIRecommendationCardProps) {
  const isSell = data.action === "sell";
  const accentColor = isSell ? "emerald" : "amber";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className={cn(
        "relative overflow-hidden rounded-xl border p-4",
        isSell
          ? "border-emerald-500/30 bg-gradient-to-br from-emerald-500/5 to-emerald-500/10"
          : "border-amber-500/30 bg-gradient-to-br from-amber-500/5 to-amber-500/10"
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg",
              isSell ? "bg-emerald-500/20 text-emerald-500" : "bg-amber-500/20 text-amber-500"
            )}
          >
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">AI Recommendation</h3>
            <p className="text-[10px] text-muted-foreground">Smart Selling Advice</p>
          </div>
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold",
            isSell
              ? "bg-emerald-500/20 text-emerald-500"
              : "bg-amber-500/20 text-amber-500"
          )}
        >
          {isSell ? (
            <>
              <CheckCircle2 className="h-3 w-3" /> Sell Now
            </>
          ) : (
            <>
              <Clock className="h-3 w-3" /> Wait
            </>
          )}
        </span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="rounded-lg bg-background/50 p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Current Price</p>
          <p className="mt-0.5 text-lg font-bold text-foreground">{formatCurrency(data.currentPrice)}</p>
        </div>
        <div className="rounded-lg bg-background/50 p-3">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Predicted (7d)</p>
          <p className={cn(
            "mt-0.5 text-lg font-bold",
            data.predictedPrice >= data.currentPrice ? "text-emerald-500" : "text-red-500"
          )}>
            {formatCurrency(data.predictedPrice)}
          </p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between rounded-lg bg-background/50 px-3 py-2">
        <span className="text-xs text-muted-foreground">Confidence Score</span>
        <div className="flex items-center gap-2">
          <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${data.confidence}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className={cn(
                "h-full rounded-full",
                data.confidence >= 80
                  ? "bg-emerald-500"
                  : data.confidence >= 60
                  ? "bg-amber-500"
                  : "bg-red-500"
              )}
            />
          </div>
          <span className="text-xs font-semibold text-foreground">{data.confidence}%</span>
        </div>
      </div>

      <div className="mt-3 space-y-1">
        {data.reasoning.map((r, i) => (
          <div key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
            <TrendingUp className="mt-0.5 h-3 w-3 shrink-0 text-primary" />
            <span>{r}</span>
          </div>
        ))}
      </div>

      <div className="mt-3 border-t border-border/50 pt-3">
        <p className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Factors Considered</p>
        <div className="flex flex-wrap gap-2">
          {data.factors.map((f) => {
            const Icon = factorIcons[f.name] ?? AlertTriangle;
            return (
              <span
                key={f.name}
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium",
                  f.impact === "positive"
                    ? "bg-emerald-500/10 text-emerald-500"
                    : f.impact === "negative"
                    ? "bg-red-500/10 text-red-500"
                    : "bg-muted text-muted-foreground"
                )}
              >
                <Icon className="h-3 w-3" />
                {f.name}
              </span>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
