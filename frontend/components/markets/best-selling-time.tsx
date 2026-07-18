"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SellingWindow } from "@/lib/markets-data";

interface BestSellingTimeProps {
  data: SellingWindow[];
}

const months = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function BestSellingTime({ data }: BestSellingTimeProps) {
  const [monthOffset, setMonthOffset] = useState(0);

  const currentDate = new Date(2026, 6 + monthOffset, 1);
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  const monthName = months[month];

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfWeek = new Date(year, month, 1).getDay();

  const getScore = (day: number): SellingWindow["score"] => {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    return data.find((d) => d.date === dateStr)?.score ?? "good";
  };

  const scoreColors: Record<SellingWindow["score"], string> = {
    best: "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
    good: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
    avoid: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
  };

  const scoreLabels: Record<SellingWindow["score"], string> = {
    best: "Best",
    good: "Good",
    avoid: "Avoid",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="rounded-xl border border-border bg-card p-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CalendarIcon className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold text-foreground">Best Selling Time</h3>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setMonthOffset((o) => Math.max(-6, o - 1))}
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <span className="w-24 text-center text-xs font-medium text-foreground">
            {monthName} {year}
          </span>
          <button
            onClick={() => setMonthOffset((o) => Math.min(6, o + 1))}
            className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="mt-3 flex gap-2">
        {(["best", "good", "avoid"] as const).map((s) => (
          <div key={s} className="flex items-center gap-1.5">
            <div className={cn("h-2.5 w-2.5 rounded-sm", scoreColors[s].split(" ")[0])} />
            <span className="text-[10px] text-muted-foreground">{scoreLabels[s]}</span>
          </div>
        ))}
      </div>

      <div className="mt-3">
        <div className="grid grid-cols-7 gap-1">
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
            <div key={d} className="py-1 text-center text-[10px] font-medium text-muted-foreground">
              {d}
            </div>
          ))}
          {Array.from({ length: firstDayOfWeek }).map((_, i) => (
            <div key={`empty-${i}`} />
          ))}
          {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
            const score = getScore(day);
            return (
              <motion.button
                key={day}
                whileHover={{ scale: 1.1 }}
                className={cn(
                  "flex h-8 w-full items-center justify-center rounded-md border text-xs font-medium transition-colors",
                  scoreColors[score]
                )}
              >
                {day}
              </motion.button>
            );
          })}
        </div>
      </div>

      <p className="mt-3 text-[10px] text-muted-foreground text-center">
        Green days indicate optimal selling windows based on market trends and demand forecasts.
      </p>
    </motion.div>
  );
}
