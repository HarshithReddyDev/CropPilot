"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";

export function DemoBanner() {
  const router = useRouter();
  const { isDemoMode, disableDemoMode } = useAuth();
  const [dismissed, setDismissed] = useState(false);

  if (!isDemoMode || dismissed) return null;

  const handleExit = () => {
    disableDemoMode();
    setDismissed(true);
    router.push("/");
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -40 }}
        transition={{ type: "spring", stiffness: 200, damping: 25 }}
        className="relative overflow-hidden rounded-xl bg-gradient-to-r from-emerald-500/10 via-emerald-500/5 to-emerald-500/10 border border-emerald-500/20 px-4 py-3"
      >
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,hsl(var(--primary)/0.08),transparent_60%)]" />
        <div className="relative flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-emerald-500 shrink-0" />
            <p className="text-sm font-medium text-foreground">
              Demo Mode &mdash; You&apos;re viewing CropPilot with sample data
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleExit}
              className="gap-1.5 text-xs"
            >
              <X className="h-3.5 w-3.5" />
              Exit Demo
            </Button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
