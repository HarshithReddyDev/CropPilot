"use client";

import { type ReactNode } from "react";
import { motion } from "framer-motion";
import { Sprout } from "lucide-react";

interface AuthLayoutProps {
  children: ReactNode;
}

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-primary/10 dark:from-primary/10 dark:via-background dark:to-primary/5" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,hsl(var(--primary)/0.08),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,hsl(var(--primary)/0.05),transparent_50%)]" />
      <div className="grid min-h-screen lg:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="relative z-10 flex items-center justify-center px-6 py-12"
        >
          <div className="w-full max-w-md">
            <div className="mb-8 flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Sprout className="h-5 w-5" />
              </div>
              <span className="text-xl font-bold text-foreground">CropPilot</span>
            </div>
            {children}
          </div>
        </motion.div>
        <div className="relative hidden items-center justify-center overflow-hidden bg-gradient-to-br from-primary/20 via-primary/10 to-background lg:flex">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative"
          >
            <div className="relative rounded-2xl border border-border/50 bg-card/30 p-2 shadow-2xl backdrop-blur-sm">
              <div className="rounded-xl bg-gradient-to-br from-muted to-background p-8 text-center">
                <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-emerald-400 shadow-lg">
                  <Sprout className="h-12 w-12 text-white" />
                </div>
                <h2 className="mt-6 text-2xl font-bold text-foreground">Welcome to CropPilot</h2>
                <p className="mt-3 max-w-sm text-muted-foreground">
                  AI-powered platform for modern farming — crop monitoring, disease detection, weather intelligence, market insights, and government schemes.
                </p>
                <div className="mt-8 grid grid-cols-3 gap-4">
                  {[
                    { label: "Farmers", value: "10K+" },
                    { label: "Crops", value: "50+" },
                    { label: "Coverage", value: "All India" },
                  ].map(({ label, value }) => (
                    <div key={label} className="rounded-lg bg-background/50 p-3">
                      <p className="text-lg font-bold text-foreground">{value}</p>
                      <p className="text-xs text-muted-foreground">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="absolute -bottom-4 -left-4 rounded-xl border border-border/50 bg-card p-3 shadow-lg">
              <p className="text-sm font-medium text-foreground">🌾 Smart Farming</p>
              <p className="text-xs text-muted-foreground">AI-Driven Insights</p>
            </div>
            <div className="absolute -right-4 -top-4 rounded-xl border border-border/50 bg-card p-3 shadow-lg">
              <p className="text-sm font-medium text-foreground">📈 Market Intel</p>
              <p className="text-xs text-muted-foreground">Real-time Prices</p>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
