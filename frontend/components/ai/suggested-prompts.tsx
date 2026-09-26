"use client";

import { motion } from "framer-motion";
import {
  Sprout,
  Bug,
  TrendingUp,
  Landmark,
  CloudSun,
  Tractor,
} from "lucide-react";
import { useTranslation } from "@/lib/i18n";

const prompts = [
  {
    icon: Sprout,
    titleKey: "assistant.cardCrop",
    bodyKey: "assistant.cardCropBody",
    queryKey: "assistant.cardCropQuery",
    color: "text-emerald-500",
    bgColor: "bg-emerald-500/10",
  },
  {
    icon: Bug,
    titleKey: "assistant.cardDisease",
    bodyKey: "assistant.cardDiseaseBody",
    queryKey: "assistant.cardDiseaseQuery",
    color: "text-rose-500",
    bgColor: "bg-rose-500/10",
  },
  {
    icon: TrendingUp,
    titleKey: "assistant.cardMarket",
    bodyKey: "assistant.cardMarketBody",
    queryKey: "assistant.cardMarketQuery",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  {
    icon: Landmark,
    titleKey: "assistant.cardScheme",
    bodyKey: "assistant.cardSchemeBody",
    queryKey: "assistant.cardSchemeQuery",
    color: "text-amber-500",
    bgColor: "bg-amber-500/10",
  },
  {
    icon: CloudSun,
    titleKey: "assistant.cardWeather",
    bodyKey: "assistant.cardWeatherBody",
    queryKey: "assistant.cardWeatherQuery",
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
  },
  {
    icon: Tractor,
    titleKey: "assistant.cardPlan",
    bodyKey: "assistant.cardPlanBody",
    queryKey: "assistant.cardPlanQuery",
    color: "text-violet-500",
    bgColor: "bg-violet-500/10",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20, scale: 0.95 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.35, ease: "easeOut" },
  },
};

interface SuggestedPromptsProps {
  onSelect: (prompt: string) => void;
}

export function SuggestedPrompts({ onSelect }: SuggestedPromptsProps) {
  const { t } = useTranslation();
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="w-full max-w-2xl mx-auto"
    >
      <motion.p
        variants={itemVariants}
        className="text-center text-sm text-muted-foreground mb-6"
      >
        {t("assistant.suggestTitle")}
      </motion.p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {prompts.map((prompt) => {
          const Icon = prompt.icon;
          return (
            <motion.button
              key={prompt.titleKey}
              variants={itemVariants}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(t(prompt.queryKey))}
              className="group flex flex-col items-start gap-3 rounded-xl border border-border bg-card/50 p-4 text-start transition-colors hover:border-primary/30 hover:bg-card hover:shadow-md"
            >
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-lg ${prompt.bgColor}`}
              >
                <Icon className={`h-5 w-5 ${prompt.color}`} />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                  {t(prompt.titleKey)}
                </h4>
                <p className="mt-0.5 text-xs text-muted-foreground line-clamp-1">
                  {t(prompt.bodyKey)}
                </p>
              </div>
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}
