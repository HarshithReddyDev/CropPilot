"use client";

import { ExternalLink, CheckCircle2, FileText, ListOrdered, Coins, Calendar } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { GovernmentScheme } from "@/types";

const categoryColors: Record<string, string> = {
  Insurance: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  "Income Support": "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  Investment: "bg-violet-500/10 text-violet-600 dark:text-violet-400 border-violet-500/20",
  "Soil Health": "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
  Market: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20",
};

interface SchemeDetailProps {
  scheme: GovernmentScheme | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SchemeDetail({ scheme, open, onOpenChange }: SchemeDetailProps) {
  if (!scheme) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <div className="flex items-center gap-2">
            {scheme.scheme_code && (
              <Badge variant="outline" className="text-xs font-mono">{scheme.scheme_code}</Badge>
            )}
            <Badge
              className={cn(
                "border text-xs",
                categoryColors[scheme.category ?? ""] ?? "bg-muted text-muted-foreground"
              )}
            >
              {scheme.category}
            </Badge>
          </div>
          <DialogTitle className="mt-2 text-lg">{scheme.scheme_name}</DialogTitle>
          <DialogDescription>{scheme.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {scheme.ministry && (
            <div className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2 text-sm">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">Ministry:</span>
              <span className="font-medium text-foreground">{scheme.ministry}</span>
              {scheme.department && (
                <>
                  <span className="text-muted-foreground">·</span>
                  <span className="text-muted-foreground">{scheme.department}</span>
                </>
              )}
            </div>
          )}

          {scheme.eligibility_criteria && (
            <div>
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                Eligibility Criteria
              </h4>
              <ul className="space-y-1">
                {scheme.eligibility_criteria.split("\n").map((line, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
                    {line}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {scheme.benefits && (
            <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                <Coins className="h-4 w-4" />
                Benefits
              </h4>
              <p className="text-sm text-muted-foreground whitespace-pre-line">{scheme.benefits}</p>
            </div>
          )}

          {scheme.documents_required && (
            <div>
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <FileText className="h-4 w-4 text-primary" />
                Required Documents
              </h4>
              <div className="flex flex-wrap gap-2">
                {scheme.documents_required.split(",").map((doc, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-foreground"
                  >
                    <CheckCircle2 className="h-3 w-3 text-primary" />
                    {doc.trim()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {scheme.application_process && (
            <div>
              <h4 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-foreground">
                <ListOrdered className="h-4 w-4 text-primary" />
                Application Process
              </h4>
              <ol className="space-y-1.5">
                {scheme.application_process.split("\n").map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-bold text-primary">
                      {i + 1}
                    </span>
                    {step.replace(/^\d+\.\s*/, "")}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {scheme.funding_pattern && (
            <div className="flex items-start gap-2 rounded-lg bg-muted/50 px-3 py-2">
              <Coins className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs font-medium text-muted-foreground">Funding Pattern</p>
                <p className="text-sm text-foreground">{scheme.funding_pattern}</p>
              </div>
            </div>
          )}

          {scheme.website_url && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Calendar className="h-4 w-4" />
                {scheme.is_active ? (
                  <span className="text-emerald-500 font-medium">Active</span>
                ) : (
                  <span className="text-red-500 font-medium">Inactive</span>
                )}
              </div>
              <a
                href={scheme.website_url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Button variant="default" size="sm" className="gap-1.5">
                  Apply Now
                  <ExternalLink className="h-3.5 w-3.5" />
                </Button>
              </a>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
