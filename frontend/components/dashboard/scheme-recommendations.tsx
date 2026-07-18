"use client";

import { motion } from "framer-motion";
import { Landmark, ChevronRight, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DashboardData } from "@/lib/constants";

interface SchemeRecommendationsProps {
  data: DashboardData["schemeRecommendations"];
  className?: string;
}

export function SchemeRecommendations({ data, className }: SchemeRecommendationsProps) {
  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center gap-2 mb-4">
        <Landmark className="h-5 w-5 text-primary" />
        <h3 className="font-semibold text-sm">Scheme Recommendations</h3>
      </div>

      <div className="space-y-3">
        {data.map((scheme, i) => (
          <motion.div
            key={scheme.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08, duration: 0.25 }}
            className="rounded-lg border border-border p-3 hover:bg-accent/50 transition-colors cursor-pointer"
          >
            <div className="flex items-start justify-between mb-1">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary mt-0.5 shrink-0" />
                <h4 className="text-sm font-medium">{scheme.name}</h4>
              </div>
              <Button variant="ghost" size="icon" className="h-6 w-6 -mr-1">
                <ChevronRight className="h-3.5 w-3.5" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground ml-6 mb-2">{scheme.description}</p>
            <div className="ml-6 space-y-1">
              <div>
                <span className="text-[10px] font-medium text-muted-foreground uppercase">Eligibility</span>
                <p className="text-xs">{scheme.eligibility}</p>
              </div>
              <div>
                <span className="text-[10px] font-medium text-muted-foreground uppercase">Benefits</span>
                <p className="text-xs text-primary font-medium">{scheme.benefits}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
