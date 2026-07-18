"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  TrendingUp,
  Sprout,
  Droplets,
  FlaskConical,
  LineChart,
  Calendar,
  Download,
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { RevenueAnalytics } from "@/components/analytics/revenue-analytics";
import { YieldAnalytics } from "@/components/analytics/yield-analytics";
import { CropHealthAnalytics } from "@/components/analytics/crop-health-analytics";
import { WaterUsageAnalytics } from "@/components/analytics/water-usage-analytics";
import { FertilizerAnalytics } from "@/components/analytics/fertilizer-analytics";
import { MarketAnalytics } from "@/components/analytics/market-analytics";
import { InsightsPanel } from "@/components/analytics/insights-panel";
import { cn } from "@/lib/utils";

const tabs = [
  { id: "revenue", label: "Revenue", icon: TrendingUp },
  { id: "yield", label: "Yield", icon: BarChart3 },
  { id: "crop-health", label: "Crop Health", icon: Sprout },
  { id: "water-usage", label: "Water Usage", icon: Droplets },
  { id: "fertilizer", label: "Fertilizer Usage", icon: FlaskConical },
  { id: "market", label: "Market Analytics", icon: LineChart },
] as const;

type TabId = (typeof tabs)[number]["id"];

const dateRanges = [
  { value: "7d", label: "7D" },
  { value: "30d", label: "30D" },
  { value: "90d", label: "90D" },
  { value: "1y", label: "1Y" },
  { value: "custom", label: "Custom" },
] as const;

const stats = [
  { label: "Total Revenue", value: "₹8,92,000", trend: { value: 12.5, isPositive: true } },
  { label: "Avg Yield/ha", value: "28.3 qtl", trend: { value: 5.2, isPositive: true } },
  { label: "Health Score", value: "82/100", trend: { value: 3.1, isPositive: true } },
  { label: "Water Efficiency", value: "84%", trend: { value: 2.4, isPositive: true } },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: "easeOut" } },
};

const tabContent: Record<TabId, React.FC> = {
  revenue: RevenueAnalytics,
  yield: YieldAnalytics,
  "crop-health": CropHealthAnalytics,
  "water-usage": WaterUsageAnalytics,
  fertilizer: FertilizerAnalytics,
  market: MarketAnalytics,
};

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<TabId>("revenue");
  const [dateRange, setDateRange] = useState<string>("1y");
  const ActiveComponent = useMemo(() => tabContent[activeTab], [activeTab]);

  return (
    <DashboardLayout>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold">Analytics</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Comprehensive insights into your farm performance
            </p>
          </div>
          <div className="flex items-center gap-2">
            {dateRanges.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setDateRange(value)}
                className={cn(
                  "px-3 py-1.5 text-sm font-medium rounded-lg transition-colors",
                  dateRange === value
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-border bg-card p-4 transition-shadow hover:shadow-md"
            >
              <p className="text-sm text-muted-foreground">{stat.label}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-2xl font-bold">{stat.value}</span>
                <span
                  className={cn(
                    "text-xs font-medium px-1.5 py-0.5 rounded-full",
                    stat.trend.isPositive
                      ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/30 dark:text-emerald-400"
                      : "bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400"
                  )}
                >
                  {stat.trend.isPositive ? "+" : "-"}{stat.trend.value}%
                </span>
              </div>
            </div>
          ))}
        </motion.div>

        <motion.div variants={itemVariants} className="flex items-center gap-1 border-b border-border overflow-x-auto pb-0">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                activeTab === id
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </button>
          ))}
        </motion.div>

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          <div className="xl:col-span-3">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
              >
                <ActiveComponent />
              </motion.div>
            </AnimatePresence>
          </div>
          <div className="xl:col-span-1">
            <InsightsPanel />
          </div>
        </div>
      </motion.div>
    </DashboardLayout>
  );
}
