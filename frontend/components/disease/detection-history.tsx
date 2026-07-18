"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  ChevronRight,
  Search,
  Filter,
  AlertTriangle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils";

interface HistoryEntry {
  id: string;
  date: string;
  crop: string;
  disease: string;
  confidence: number;
  severity: "low" | "moderate" | "high" | "critical";
  status: "resolved" | "treatment" | "pending";
}

interface DetectionHistoryProps {
  entries: HistoryEntry[];
  onSelect: (entry: HistoryEntry) => void;
}

const severityColors: Record<string, string> = {
  low: "text-emerald-500 bg-emerald-500/10",
  moderate: "text-amber-500 bg-amber-500/10",
  high: "text-orange-500 bg-orange-500/10",
  critical: "text-red-500 bg-red-500/10",
};

const statusConfig = {
  resolved: { label: "Resolved", class: "text-emerald-500 bg-emerald-500/10" },
  treatment: { label: "In Treatment", class: "text-blue-500 bg-blue-500/10" },
  pending: { label: "Pending", class: "text-amber-500 bg-amber-500/10" },
};

export function DetectionHistory({
  entries,
  onSelect,
}: DetectionHistoryProps) {
  const [search, setSearch] = useState("");

  const filtered = entries.filter(
    (e) =>
      e.crop.toLowerCase().includes(search.toLowerCase()) ||
      e.disease.toLowerCase().includes(search.toLowerCase())
  );

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
            <h3 className="text-sm font-semibold text-foreground">Detection History</h3>
            <p className="text-xs text-muted-foreground">
              {entries.length} past detections
            </p>
          </div>
        </div>
      </div>

      <div className="border-b border-border/50 px-5 py-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by crop or disease..."
            className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-sm outline-none ring-1 ring-transparent transition-all placeholder:text-muted-foreground focus:ring-primary"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border/50 text-xs text-muted-foreground">
              <th className="px-5 py-3 text-left font-medium">Date</th>
              <th className="px-5 py-3 text-left font-medium">Crop</th>
              <th className="px-5 py-3 text-left font-medium">Disease</th>
              <th className="px-5 py-3 text-left font-medium">Confidence</th>
              <th className="px-5 py-3 text-left font-medium">Severity</th>
              <th className="px-5 py-3 text-left font-medium">Status</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-5 py-8 text-center text-sm text-muted-foreground">
                  No detections found
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
                    {entry.crop}
                  </td>
                  <td className="px-5 py-3 text-sm text-muted-foreground">
                    {entry.disease}
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-12 overflow-hidden rounded-full bg-muted">
                        <div
                          className={cn(
                            "h-full rounded-full",
                            entry.confidence >= 70
                              ? "bg-emerald-500"
                              : entry.confidence >= 40
                                ? "bg-amber-500"
                                : "bg-red-500"
                          )}
                          style={{ width: `${entry.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {entry.confidence}%
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3">
                    <Badge
                      className={cn(
                        "border-0 text-[10px]",
                        severityColors[entry.severity]
                      )}
                    >
                      {entry.severity.charAt(0).toUpperCase() + entry.severity.slice(1)}
                    </Badge>
                  </td>
                  <td className="px-5 py-3">
                    <Badge
                      className={cn(
                        "border-0 text-[10px]",
                        statusConfig[entry.status].class
                      )}
                    >
                      {statusConfig[entry.status].label}
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
    </motion.div>
  );
}
