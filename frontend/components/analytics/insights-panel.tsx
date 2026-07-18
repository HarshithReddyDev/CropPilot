"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Info,
  RefreshCw,
  Download,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Insight {
  id: string;
  icon: typeof Lightbulb;
  title: string;
  description: string;
  impact: "positive" | "negative" | "neutral";
  action: string;
}

const initialInsights: Insight[] = [
  {
    id: "1",
    icon: TrendingUp,
    title: "Revenue Growth Opportunity",
    description: "Cotton prices are up 12% this quarter. Consider increasing cotton acreage next season by 15% to capitalize on the trend.",
    impact: "positive",
    action: "View Market Data",
  },
  {
    id: "2",
    icon: AlertTriangle,
    title: "Water Stress Detected",
    description: "Plot A-3 (Rice) is showing signs of water stress. Current soil moisture is 28% — below the optimal 40% threshold.",
    impact: "negative",
    action: "Check Irrigation",
  },
  {
    id: "3",
    icon: CheckCircle2,
    title: "Yield Target Achieved",
    description: "Your maize yield of 3.5 t/ha exceeded the target of 3.2 t/ha by 9.4%. Best performing crop this season.",
    impact: "positive",
    action: "View Details",
  },
  {
    id: "4",
    icon: Lightbulb,
    title: "Fertilizer Optimization",
    description: "Reduce nitrogen application by 10% in Plot B-2. Soil tests show excess N levels which may lead to lodging.",
    impact: "neutral",
    action: "View Report",
  },
  {
    id: "5",
    icon: Info,
    title: "Market Timing Alert",
    description: "Rice prices expected to peak in November. Consider holding 30% of harvest for sale during peak window.",
    impact: "positive",
    action: "Price Forecast",
  },
];

const impactStyles = {
  positive: {
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    text: "text-emerald-600 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-800",
    icon: TrendingUp,
  },
  negative: {
    bg: "bg-red-50 dark:bg-red-950/30",
    text: "text-red-600 dark:text-red-400",
    border: "border-red-200 dark:border-red-800",
    icon: AlertTriangle,
  },
  neutral: {
    bg: "bg-blue-50 dark:bg-blue-950/30",
    text: "text-blue-600 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800",
    icon: Lightbulb,
  },
};

export function InsightsPanel() {
  const [insights, setInsights] = useState<Insight[]>(initialInsights);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const visibleInsights = insights.filter((i) => !dismissed.has(i.id));

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setInsights((prev) =>
        prev.map((i) => ({
          ...i,
          description: i.description + " [refreshed]",
        }))
      );
      setIsRefreshing(false);
    }, 1500);
  };

  return (
    <Card className="sticky top-6">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-amber-500" />
            <CardTitle className="text-sm">AI Insights</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin")} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <AnimatePresence mode="popLayout">
          {visibleInsights.slice(0, 4).map((insight) => {
            const style = impactStyles[insight.impact];
            const Icon = style.icon;
            return (
              <motion.div
                key={insight.id}
                layout
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20, height: 0, marginBottom: 0 }}
                transition={{ duration: 0.25 }}
                className={cn(
                  "rounded-lg border p-3 transition-all hover:shadow-sm",
                  style.bg,
                  style.border
                )}
              >
                <div className="flex items-start gap-2.5">
                  <div className={cn("mt-0.5", style.text)}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-foreground">
                      {insight.title}
                    </p>
                    <p className="text-[11px] text-muted-foreground mt-1 leading-relaxed">
                      {insight.description}
                    </p>
                    <button className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline">
                      {insight.action}
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {visibleInsights.length > 4 && (
          <p className="text-center text-xs text-muted-foreground">
            +{visibleInsights.length - 4} more insights
          </p>
        )}

        <Button className="w-full mt-2" size="sm">
          <Download className="h-4 w-4 mr-1.5" />
          Generate Report
        </Button>
      </CardContent>
    </Card>
  );
}
