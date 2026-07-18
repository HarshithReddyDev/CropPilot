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

const prompts = [
  {
    icon: Sprout,
    title: "Crop Advice",
    description: "Best practices for wheat cultivation in Punjab",
    query: "What are the best practices for wheat cultivation in Punjab?",
    color: "text-emerald-500",
    bgColor: "bg-emerald-500/10",
  },
  {
    icon: Bug,
    title: "Disease Help",
    description: "Identify and treat leaf blight in tomatoes",
    query: "How do I identify and treat leaf blight in tomato plants?",
    color: "text-rose-500",
    bgColor: "bg-rose-500/10",
  },
  {
    icon: TrendingUp,
    title: "Market Questions",
    description: "Current mandi prices for rice and wheat",
    query: "What are the current mandi prices for rice and wheat in Punjab?",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  {
    icon: Landmark,
    title: "Scheme Info",
    description: "Government schemes for small farmers",
    query: "What government schemes am I eligible for as a small farmer in India?",
    color: "text-amber-500",
    bgColor: "bg-amber-500/10",
  },
  {
    icon: CloudSun,
    title: "Weather Query",
    description: "Upcoming weather and its effect on crops",
    query: "How will the upcoming weather affect my kharif crops?",
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
  },
  {
    icon: Tractor,
    title: "Farm Planning",
    description: "Crop rotation and soil management tips",
    query: "What crop rotation should I follow for my farm?",
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
        Ask me anything about farming — crops, diseases, markets, schemes, and more
      </motion.p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {prompts.map((prompt) => {
          const Icon = prompt.icon;
          return (
            <motion.button
              key={prompt.title}
              variants={itemVariants}
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onSelect(prompt.query)}
              className="group flex flex-col items-start gap-3 rounded-xl border border-border bg-card/50 p-4 text-left transition-colors hover:border-primary/30 hover:bg-card hover:shadow-md"
            >
              <div
                className={`flex h-10 w-10 items-center justify-center rounded-lg ${prompt.bgColor}`}
              >
                <Icon className={`h-5 w-5 ${prompt.color}`} />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                  {prompt.title}
                </h4>
                <p className="mt-0.5 text-xs text-muted-foreground line-clamp-1">
                  {prompt.description}
                </p>
              </div>
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}
