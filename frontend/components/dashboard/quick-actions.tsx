"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Scan, CloudSun, TrendingUp, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useTranslation } from "@/lib/i18n";

interface QuickActionsProps {
  className?: string;
}

export function QuickActions({ className }: QuickActionsProps) {
  const { t } = useTranslation();
  const router = useRouter();

  const actions = [
    { key: "dashboard.qaScan", icon: Scan, href: "/disease-detection", color: "text-green-500", bg: "bg-green-500/10" },
    { key: "dashboard.qaWeather", icon: CloudSun, href: "/weather", color: "text-blue-500", bg: "bg-blue-500/10" },
    { key: "dashboard.qaMarkets", icon: TrendingUp, href: "/markets", color: "text-amber-500", bg: "bg-amber-500/10" },
    { key: "dashboard.qaAssistant", icon: Bot, href: "/ai-assistant", color: "text-purple-500", bg: "bg-purple-500/10" },
  ];

  return (
    <div className={cn("glass-card p-5", className)}>
      <h3 className="font-semibold text-sm mb-3">{t("dashboard.wQuickActions")}</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {actions.map((action, i) => {
          const Icon = action.icon;
          return (
            <motion.div
              key={action.key}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05, duration: 0.2 }}
            >
              <Button
                variant="outline"
                onClick={() => router.push(action.href)}
                className="flex-col h-auto py-4 gap-2 w-full hover:bg-accent transition-colors"
              >
                <div className={cn("flex h-10 w-10 items-center justify-center rounded-xl", action.bg)}>
                  <Icon className={cn("h-5 w-5", action.color)} />
                </div>
                <span className="text-xs font-medium">{t(action.key)}</span>
              </Button>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
