"use client";

import { motion } from "framer-motion";
import { Bug, AlertTriangle, Clock, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { DashboardData } from "@/lib/constants";

interface DiseaseAlertsProps {
  data: DashboardData["diseaseAlerts"];
  className?: string;
}

const severityConfig = {
  high: { label: "High", class: "bg-red-500/10 text-red-500 border-red-500/20" },
  medium: { label: "Medium", class: "bg-amber-500/10 text-amber-500 border-amber-500/20" },
  low: { label: "Low", class: "bg-green-500/10 text-green-500 border-green-500/20" },
};

export function DiseaseAlerts({ data, className }: DiseaseAlertsProps) {
  if (data.alerts.length === 0) {
    return (
      <div className={cn("glass-card p-5", className)}>
        <div className="flex items-center gap-2 mb-4">
          <Bug className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-sm">Disease Alerts</h3>
        </div>
        <div className="flex flex-col items-center justify-center py-8 text-muted-foreground">
          <Bug className="h-10 w-10 mb-2 opacity-30" />
          <p className="text-sm">No active disease alerts</p>
          <p className="text-xs">Your crops are healthy</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("glass-card p-5", className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Bug className="h-5 w-5 text-primary" />
          <h3 className="font-semibold text-sm">Disease Alerts</h3>
        </div>
        <Badge variant="destructive" size="sm">{data.total} active</Badge>
      </div>

      <div className="space-y-2">
        {data.alerts.map((alert, i) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06, duration: 0.25 }}
            className="flex items-start gap-3 rounded-lg border border-border p-3"
          >
            <AlertTriangle className={cn(
              "h-4 w-4 mt-0.5 shrink-0",
              alert.severity === "high" ? "text-red-500" : alert.severity === "medium" ? "text-amber-500" : "text-green-500"
            )} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-sm font-medium">{alert.disease}</span>
                <Badge variant="outline" size="sm" className={cn("border", severityConfig[alert.severity].class)}>
                  {severityConfig[alert.severity].label}
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground">{alert.crop} - {alert.plot}</p>
              <div className="flex items-center gap-1 mt-1">
                <Clock className="h-3 w-3 text-muted-foreground" />
                <span className="text-[10px] text-muted-foreground">{alert.time}</span>
              </div>
            </div>
            <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0">
              <ChevronRight className="h-3.5 w-3.5" />
            </Button>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
