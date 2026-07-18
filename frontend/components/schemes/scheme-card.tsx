"use client";

import { motion } from "framer-motion";
import { ExternalLink, Building2, Shield, ChevronDown } from "lucide-react";
import { cn, truncate } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import type { GovernmentScheme } from "@/types";

const categoryColors: Record<string, string> = {
  Insurance: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  "Income Support": "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  Investment: "bg-violet-500/10 text-violet-600 dark:text-violet-400 border-violet-500/20",
  "Soil Health": "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
  Market: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/20",
};

const categoryIcons: Record<string, typeof Shield> = {
  Insurance: Shield,
  "Income Support": Building2,
  Investment: Building2,
  "Soil Health": Shield,
  Market: Building2,
};

interface SchemeCardProps {
  scheme: GovernmentScheme;
  onViewDetail: (scheme: GovernmentScheme) => void;
}

export function SchemeCard({ scheme, onViewDetail }: SchemeCardProps) {
  const Icon = categoryIcons[scheme.category ?? ""] ?? Shield;
  const eligibilityBullets = scheme.eligibility_criteria
    ? scheme.eligibility_criteria.split(".").filter(Boolean).slice(0, 3)
    : [];

  const benefitHighlight = scheme.benefits
    ? scheme.benefits.split(".").find((s) => s.match(/[₹\d]/)) ?? scheme.benefits.split(".")[0]
    : "";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, transition: { type: "spring", stiffness: 300, damping: 20 } }}
      className="group rounded-xl border border-border/50 bg-card transition-shadow hover:shadow-xl hover:shadow-primary/5"
    >
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              "flex h-10 w-10 items-center justify-center rounded-lg",
              categoryColors[scheme.category ?? ""] ?? "bg-muted text-muted-foreground"
            )}>
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground leading-snug">{scheme.scheme_name}</h3>
              {scheme.scheme_code && (
                <p className="text-xs text-muted-foreground font-mono mt-0.5">{scheme.scheme_code}</p>
              )}
            </div>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap gap-1.5">
          {scheme.category && (
            <Badge className={cn("border text-[10px]", categoryColors[scheme.category])} size="sm">
              {scheme.category}
            </Badge>
          )}
          {scheme.ministry && (
            <Badge variant="secondary" size="sm" className="text-[10px]">
              {scheme.ministry.split(" ").slice(0, 3).join(" ")}...
            </Badge>
          )}
        </div>

        <p className="mt-3 text-xs text-muted-foreground leading-relaxed">
          {truncate(scheme.description, 120)}
        </p>

        {eligibilityBullets.length > 0 && (
          <div className="mt-3 space-y-1">
            <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">Eligibility</p>
            {eligibilityBullets.map((bullet, i) => (
              <p key={i} className="flex items-start gap-1.5 text-[11px] text-muted-foreground">
                <span className="mt-0.5 h-1 w-1 shrink-0 rounded-full bg-primary/50" />
                {bullet.trim().slice(0, 60)}
              </p>
            ))}
          </div>
        )}

        {benefitHighlight && (
          <div className="mt-3 rounded-lg bg-primary/5 border border-primary/10 px-3 py-2">
            <p className="text-[10px] font-medium uppercase tracking-wider text-primary">Key Benefit</p>
            <p className="mt-0.5 text-xs font-medium text-foreground">{benefitHighlight.slice(0, 80)}</p>
          </div>
        )}

        <Accordion type="single" collapsible className="mt-3">
          <AccordionItem value="details" className="border-none">
            <AccordionTrigger className="py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground no-underline hover:no-underline">
              More Details
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2 text-xs text-muted-foreground">
                {scheme.application_process && (
                  <div>
                    <p className="font-medium text-foreground">Application Process:</p>
                    <p className="mt-0.5">{scheme.application_process.split("\n").slice(0, 3).join(" → ")}</p>
                  </div>
                )}
                {scheme.funding_pattern && (
                  <div>
                    <p className="font-medium text-foreground">Funding:</p>
                    <p className="mt-0.5">{scheme.funding_pattern}</p>
                  </div>
                )}
                {scheme.documents_required && (
                  <div>
                    <p className="font-medium text-foreground">Documents:</p>
                    <p className="mt-0.5">{scheme.documents_required.split(",").slice(0, 4).map((d) => d.trim()).join(", ")}</p>
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>

        <div className="mt-4 flex items-center gap-2">
          <Button
            size="sm"
            className="flex-1 gap-1"
            onClick={() => onViewDetail(scheme)}
          >
            Check Eligibility
          </Button>
          {scheme.website_url && (
            <a
              href={scheme.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-input bg-background text-muted-foreground transition-colors hover:text-foreground"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
}
