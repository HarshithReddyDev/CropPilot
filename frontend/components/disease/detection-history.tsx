"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  ChevronRight,
  Search,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";
import type { ConfidenceBand, CropStatus, DiagnosisStatus, ReasonCode } from "@/services/disease";

/**
 * Session-only history: metadata from analyses run in this browser session.
 * Images are never retained (see note below the table). Entries are keyed
 * by backend request_id: one analysis request yields exactly one row, and a
 * re-delivered result updates its row instead of duplicating it.
 */
export interface SessionHistoryEntry {
  id: string;
  date: string;
  crop: string | null;
  cropStatus: CropStatus;
  disease: string | null;
  band: ConfidenceBand | null;
  status: DiagnosisStatus;
  reason: ReasonCode | null;
}

interface DetectionHistoryProps {
  entries: SessionHistoryEntry[];
  onSelect: (entry: SessionHistoryEntry) => void;
}

const BAND_STYLE: Record<ConfidenceBand, string> = {
  high: "text-emerald-500 bg-emerald-500/10",
  medium: "text-amber-500 bg-amber-500/10",
  low: "text-orange-500 bg-orange-500/10",
  unverified: "text-slate-500 bg-slate-500/10",
  unknown: "text-slate-500 bg-slate-500/10",
};

const BAND_KEYS: Record<ConfidenceBand, string> = {
  high: "disease.bandHigh",
  medium: "disease.bandMedium",
  low: "disease.bandLow",
  unverified: "disease.bandUnverified",
  unknown: "disease.bandUnknown",
};

const STATUS_KEYS: Record<string, string> = {
  diagnosed: "disease.statusDiagnosed",
  probable: "disease.statusProbable",
  uncertain: "disease.statusUncertain",
  insufficient_image: "disease.statusInsufficientImage",
  unsupported_crop: "disease.statusNotSupported",
  error: "disease.statusFailed",
};

function statusKey(entry: SessionHistoryEntry): string {
  if (entry.status === "unsupported_crop") return "disease.statusNotSupported";
  if (entry.status === "error") return "disease.statusFailed";
  return STATUS_KEYS[entry.status] ?? "disease.statusUncertain";
}

export function DetectionHistory({
  entries,
  onSelect,
}: DetectionHistoryProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");

  const filtered = entries.filter((e) => {
    const crop = e.crop ?? t("disease.cropNotIdentified");
    const disease = e.disease ?? t("disease.noDiagnosis");
    return (
      crop.toLowerCase().includes(search.toLowerCase()) ||
      disease.toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card overflow-hidden"
    >
      <div className="flex items-center justify-between border-b border-border/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Clock className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-foreground">{t("disease.historyTitle")}</h3>
            <p className="text-xs text-muted-foreground">
              {t("disease.pastDetections", { count: entries.length })}
            </p>
          </div>
        </div>
      </div>

      <div className="border-b border-border/50 px-5 py-3">
        <div className="relative">
          <Search className="absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t("disease.searchHistory")}
            aria-label={t("disease.searchHistory")}
            className="w-full rounded-lg border border-border bg-background py-2 ps-9 pe-3 text-sm outline-none ring-1 ring-transparent transition-all placeholder:text-muted-foreground focus:ring-primary"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border/50 text-xs text-muted-foreground">
              <th className="px-5 py-3 text-start font-medium">{t("disease.thDate")}</th>
              <th className="px-5 py-3 text-start font-medium">{t("disease.thCrop")}</th>
              <th className="px-5 py-3 text-start font-medium">{t("disease.thDisease")}</th>
              <th className="px-5 py-3 text-start font-medium">{t("disease.thConfidence")}</th>
              <th className="px-5 py-3 text-start font-medium">{t("disease.thStatus")}</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-8 text-center text-sm text-muted-foreground">
                  {t("disease.noDetections")}
                </td>
              </tr>
            ) : (
              filtered.map((entry, i) => (
                <motion.tr
                  key={entry.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  onClick={() => onSelect(entry)}
                  className="cursor-pointer border-b border-border/30 transition-colors hover:bg-muted/30 last:border-0"
                >
                  <td className="px-5 py-3 text-sm text-foreground">
                    {formatDate(entry.date)}
                  </td>
                  <td className="px-5 py-3 text-sm font-medium text-foreground">
                    {entry.crop ?? t("disease.cropNotIdentified")}
                  </td>
                  <td className="px-5 py-3 text-sm text-muted-foreground">
                    {entry.disease ?? t("disease.noDiagnosis")}
                  </td>
                  <td className="px-5 py-3">
                    {entry.band ? (
                      <Badge className={cn("border-0 text-[10px]", BAND_STYLE[entry.band])}>
                        {t(BAND_KEYS[entry.band])}
                      </Badge>
                    ) : (
                      <span className="text-xs text-muted-foreground">
                        {t("disease.confidenceNotAvailable")}
                      </span>
                    )}
                  </td>
                  <td className="px-5 py-3">
                    <Badge variant="outline" className="text-[10px]">
                      {t(statusKey(entry))}
                    </Badge>
                  </td>
                  <td className="px-5 py-3">
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="border-t border-border/50 px-5 py-3 text-[11px] text-muted-foreground">
        {t("disease.imageNotRetained")}
      </p>
    </motion.div>
  );
}
