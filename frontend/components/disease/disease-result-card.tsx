"use client";

import { useState } from "react";
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
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";
import type { ConfidenceBand, DiseaseAnalysis } from "@/services/disease";

interface DiseaseResultCardProps {
  result: DiseaseAnalysis;
  imageUrl?: string;
}

const BAND_KEYS: Record<ConfidenceBand, string> = {
  high: "disease.bandHigh",
  medium: "disease.bandMedium",
  low: "disease.bandLow",
  unverified: "disease.bandUnverified",
  unknown: "disease.bandUnknown",
};

const BAND_STYLE: Record<ConfidenceBand, string> = {
  high: "text-emerald-500 bg-emerald-500/10",
  medium: "text-amber-500 bg-amber-500/10",
  low: "text-orange-500 bg-orange-500/10",
  unverified: "text-slate-500 bg-slate-500/10",
  unknown: "text-slate-500 bg-slate-500/10",
};

const STATUS_KEYS: Record<string, string> = {
  diagnosed: "disease.statusDiagnosed",
  probable: "disease.statusProbable",
  uncertain: "disease.statusUncertain",
  insufficient_image: "disease.statusInsufficientImage",
  unsupported_crop: "disease.statusUnsupportedCrop",
  error: "disease.statusError",
};

/**
 * Diagnosis card. Rendered ONLY when real specialists produced findings for
 * a diagnosed/probable status. Uncertain and no-coverage states are handled
 * by the page variant panels, never here.
 */
export function DiseaseResultCard({ result, imageUrl }: DiseaseResultCardProps) {
  const { t } = useTranslation();
  const [notice, setNotice] = useState<string | null>(null);
  const top = result.findings[0];
  if (!top) return null;
  const band = top.confidence_band as ConfidenceBand;

  // Only detector outputs carry real bounding boxes. Classifier regions
  // (full / center_crop) must never be drawn as lesion locations.
  const detectorBoxes = [top, ...result.alternatives].filter(
    (f) => f.region.kind === "detector"
  );

  const summaryText = () => {
    // When the crop was never identified, the summary must not present a
    // raw model class as the diagnosis. Raw outputs go in a labeled
    // technical section instead.
    const cropUnknown = result.crop.source === "unknown";
    const lines = [
      "CropPilot Disease Analysis",
      `${t("disease.analysisStatusLabel")}: ${t(STATUS_KEYS[result.status] ?? "disease.statusUncertain")}`,
      cropUnknown
        ? `${t("disease.noVerifiedDiagnosis")}`
        : `${t("disease.detectedDisease")}: ${top.display_name}`,
      `${t("disease.confidence")}: ${cropUnknown ? t("disease.confidenceNotAvailable") : `${t(BAND_KEYS[band])} (${t("disease.calibrationUnavailable")})`}`,
      `${t("disease.cropLabel")}: ${result.crop.name ?? t("disease.cropNotIdentified")}`,
      `${t("disease.imageQuality")}: ${result.image_quality.status}`,
      `${t("disease.modelsUsed")}: ${result.routing.specialists_run.join(", ") || t("disease.specialistsNone")}`,
      `${t("disease.fieldValidation")}: ${top.field_validation}`,
      result.next_action,
    ];
    if (cropUnknown) {
      lines.push(
        `${t("disease.modelOutputs")}:`,
        ...[...result.findings, ...result.alternatives].map(
          (f) => `- ${f.display_name}: ${t("disease.rawScoreLabel")} ${f.raw_score !== null ? f.raw_score.toFixed(3) : "—"}`
        ),
        t("disease.modelOutputsInterpretation")
      );
    }
    return lines.join("\n");
  };

  const handleExport = () => {
    const blob = new Blob([summaryText()], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `croppilot-disease-analysis-${result.request_id.slice(0, 8)}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    const text = summaryText();
    try {
      if (navigator.share) {
        await navigator.share({ title: "CropPilot Disease Analysis", text });
        return;
      }
      throw new Error("no-share");
    } catch {
      try {
        await navigator.clipboard.writeText(text);
        setNotice(t("disease.summaryCopied"));
      } catch {
        setNotice(null);
      }
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <div className="flex items-center justify-between border-b border-border/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-rose-500/10 text-rose-500">
            <Bug className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">{t("disease.resultTitle")}</h3>
            <p className="text-xs text-muted-foreground">{t("disease.aiAnalysis")}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="icon" onClick={handleExport} aria-label={t("disease.downloadSummary")}>
            <Download className="h-4 w-4" aria-hidden="true" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleShare} aria-label={t("disease.shareSummary")}>
            <Share2 className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {notice && (
          <p className="rounded-lg bg-muted/50 px-4 py-2 text-xs text-muted-foreground">
            {notice}
          </p>
        )}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">{t("disease.detectedDisease")}</p>
            <p className="text-lg font-bold text-foreground">{top.display_name}</p>
            <p className="text-xs text-muted-foreground">
              {t(STATUS_KEYS[result.status] ?? "disease.statusUncertain")}
            </p>
          </div>
          <Badge className={cn("gap-1.5 border-0", BAND_STYLE[band])}>
            <AlertTriangle className="h-3 w-3" aria-hidden="true" />
            {t(BAND_KEYS[band])}
          </Badge>
        </div>

        {top.raw_score !== null && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">{t("disease.uncalibratedScore")}</span>
              <span className="font-semibold text-foreground">
                {(top.raw_score * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground">
              {t("disease.uncalibratedScoreHint")}
            </p>
          </div>
        )}

        {result.crop.source !== "unknown" && result.alternatives.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">{t("disease.possibleCauses")}</p>
            <div className="flex flex-wrap gap-2">
              {result.alternatives.map((a) => (
                <Badge key={a.disease_id} variant="secondary" className="text-[10px]">
                  {a.display_name}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {imageUrl && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <ScrollText className="h-4 w-4" aria-hidden="true" />
              <span>{t("disease.uploadedPhoto")}</span>
            </div>
            <div className="relative overflow-hidden rounded-xl bg-muted">
              <img
                src={imageUrl}
                alt={t("disease.uploadedPhoto")}
                className="h-48 w-full object-cover"
              />
              {detectorBoxes.map((f) => (
                <div
                  key={f.disease_id}
                  className="absolute border-2 border-rose-500 bg-rose-500/10 pointer-events-none"
                  style={{
                    left: `${f.region.x1 * 100}%`,
                    top: `${f.region.y1 * 100}%`,
                    width: `${Math.max(0, f.region.x2 - f.region.x1) * 100}%`,
                    height: `${Math.max(0, f.region.y2 - f.region.y1) * 100}%`,
                  }}
                >
                  <span className="absolute -top-5 left-0 rounded bg-rose-500 px-1.5 py-0.5 text-[10px] font-medium text-white whitespace-nowrap">
                    {f.display_name}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <Separator />

        <p className="rounded-lg bg-muted/50 px-4 py-3 text-sm text-muted-foreground">
          {result.next_action}
        </p>
      </div>
    </motion.div>
  );
}
