"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  Download,
  Share2,
  ScrollText,
  Bug,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

interface DetectionResult {
  disease: string;
  confidence: number;
  severity: "low" | "moderate" | "high" | "critical";
  boundingBoxes: { x: number; y: number; width: number; height: number; label: string }[];
  imageUrl?: string;
}

interface DiseaseResultCardProps {
  result: DetectionResult;
  onExport?: () => void;
  onShare?: () => void;
}

const severityConfig = {
  low: { color: "text-emerald-500", bg: "bg-emerald-500/10", label: "Low" },
  moderate: { color: "text-amber-500", bg: "bg-amber-500/10", label: "Moderate" },
  high: { color: "text-orange-500", bg: "bg-orange-500/10", label: "High" },
  critical: { color: "text-red-500", bg: "bg-red-500/10", label: "Critical" },
};

export function DiseaseResultCard({
  result,
  onExport,
  onShare,
}: DiseaseResultCardProps) {
  const sev = severityConfig[result.severity];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <div className="flex items-center justify-between border-b border-border/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-500/10 text-rose-500">
            <Bug className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">Detection Result</h3>
            <p className="text-xs text-muted-foreground">AI-powered analysis</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="icon" onClick={onExport}>
            <Download className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={onShare}>
            <Share2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="p-5 space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Detected Disease</p>
            <p className="text-lg font-bold text-foreground">{result.disease}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={cn("gap-1.5 border-0", sev.bg, sev.color)}>
              <AlertTriangle className="h-3 w-3" />
              {sev.label}
            </Badge>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Confidence Score</span>
            <span className="font-semibold text-foreground">
              {(result.confidence * 100).toFixed(1)}%
            </span>
          </div>
          <Progress value={result.confidence * 100} className="h-2" />
        </div>

        {result.imageUrl && result.boundingBoxes.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <ScrollText className="h-4 w-4" />
              <span>Detected Regions</span>
            </div>
            <div className="relative overflow-hidden rounded-xl bg-muted">
              <img
                src={result.imageUrl}
                alt="Analysis"
                className="h-48 w-full object-cover"
              />
              {result.boundingBoxes.map((box, i) => (
                <div
                  key={i}
                  className="absolute border-2 border-rose-500 bg-rose-500/10 pointer-events-none"
                  style={{
                    left: `${box.x * 100}%`,
                    top: `${box.y * 100}%`,
                    width: `${box.width * 100}%`,
                    height: `${box.height * 100}%`,
                  }}
                >
                  <span className="absolute -top-5 left-0 rounded bg-rose-500 px-1.5 py-0.5 text-[10px] font-medium text-white whitespace-nowrap">
                    {box.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <Separator />

        <div className="flex items-center justify-between rounded-lg bg-muted/50 px-4 py-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ScrollText className="h-4 w-4" />
            <span>Treatment recommendation available</span>
          </div>
          <Badge variant="outline" className="text-[10px]">
            View Below
          </Badge>
        </div>
      </div>
    </motion.div>
  );
}
