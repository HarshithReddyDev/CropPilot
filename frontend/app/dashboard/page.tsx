"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { User, CalendarDays, ChevronDown } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { FarmOverview } from "@/components/dashboard/farm-overview";
import { WeatherWidget } from "@/components/dashboard/weather-widget";
import { CropHealth } from "@/components/dashboard/crop-health";
import { DiseaseAlerts } from "@/components/dashboard/disease-alerts";
import { NotificationsWidget } from "@/components/dashboard/notifications-widget";
import { RevenueCard } from "@/components/dashboard/revenue-card";
import { ExpensesCard } from "@/components/dashboard/expenses-card";
import { ProfitCard } from "@/components/dashboard/profit-card";
import { YieldCard } from "@/components/dashboard/yield-card";
import { MarketTrends } from "@/components/dashboard/market-trends";
import { SchemeRecommendations } from "@/components/dashboard/scheme-recommendations";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { DemoBanner } from "@/app/dashboard/demo-banner";
import { useAuthStore } from "@/stores/auth-store";
import { MOCK_DASHBOARD_DATA } from "@/lib/constants";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const farms = [
  { value: "all", label: "All Farms" },
  { value: "farm-1", label: "Green Valley Farm" },
  { value: "farm-2", label: "Sunrise Fields" },
  { value: "farm-3", label: "Riverbend Estate" },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: "easeOut" },
  },
};

const today = new Date().toLocaleDateString("en-IN", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
});

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [selectedFarm, setSelectedFarm] = useState("all");
  const data = useMemo(() => MOCK_DASHBOARD_DATA, []);

  return (
    <DashboardLayout>
      <motion.div
        className="space-y-6"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <DemoBanner />

        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              <h1 className="text-xl font-bold">
                Welcome back, {user?.full_name?.split(" ")[0] || "Farmer"}
              </h1>
            </div>
            <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
              <CalendarDays className="h-4 w-4" />
              {today}
            </div>
          </div>
          <Select value={selectedFarm} onValueChange={setSelectedFarm}>
            <SelectTrigger className="w-full sm:w-[200px]">
              <SelectValue placeholder="Select farm" />
            </SelectTrigger>
            <SelectContent>
              {farms.map((farm) => (
                <SelectItem key={farm.value} value={farm.value}>
                  {farm.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </motion.div>

        <motion.div variants={itemVariants}>
          <QuickActions />
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <FarmOverview data={data.farmOverview} />
          </motion.div>
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <WeatherWidget data={data.weather} />
          </motion.div>
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <CropHealth data={data.cropHealth} />
          </motion.div>
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <DiseaseAlerts data={data.diseaseAlerts} />
          </motion.div>
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <RevenueCard data={data.revenue} />
          </motion.div>
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <ExpensesCard data={data.expenses} />
          </motion.div>
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <ProfitCard data={data.profit} />
          </motion.div>
          <motion.div variants={itemVariants} className="lg:col-span-1">
            <YieldCard data={data.yield} />
          </motion.div>
          <motion.div variants={itemVariants} className="md:col-span-2">
            <MarketTrends data={data.marketTrends} />
          </motion.div>
          <motion.div variants={itemVariants} className="md:col-span-2">
            <SchemeRecommendations data={data.schemeRecommendations} />
          </motion.div>
          <motion.div variants={itemVariants} className="md:col-span-2">
            <NotificationsWidget data={data.notifications} />
          </motion.div>
        </div>
      </motion.div>
    </DashboardLayout>
  );
}
