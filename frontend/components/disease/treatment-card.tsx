"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ListChecks,
  ShieldCheck,
  Sprout,
} from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { useTranslation } from "@/lib/i18n";
import type { KnowledgeItem } from "@/services/disease";

interface TreatmentCardProps {
  knowledge: KnowledgeItem[];
}

/** Renders only retrieved guidance. Never invents pesticide names/doses. */
export function TreatmentCard({ knowledge }: TreatmentCardProps) {
  const { t } = useTranslation();

  if (knowledge.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-5"
      >
        <p className="text-sm text-muted-foreground">{t("disease.noGuidance")}</p>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {knowledge.map((k) => (
        <motion.div
          key={k.disease_id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card overflow-hidden"
        >
          <div className="border-b border-border/50 bg-gradient-to-r from-rose-500/5 to-amber-500/5 px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-amber-500/10 text-amber-500">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">
                  {t("disease.treatmentAvailable")}
                </h3>
                <p className="text-xs text-muted-foreground">
                  {t("disease.guidanceFor")}{" "}
                  <span className="font-medium text-foreground">{k.title}</span>
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-5 p-5">
            {k.symptoms.length > 0 && (
              <Section icon={ListChecks} title={t("disease.symptoms")} color="text-rose-500">
                <ul className="space-y-1.5">
                  {k.symptoms.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-400" />
                      {s}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {k.similar_conditions.length > 0 && (
              <>
                <Separator />
                <Section icon={Sprout} title={t("disease.similarConditions")} color="text-violet-500">
                  <ul className="space-y-1.5">
                    {k.similar_conditions.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </Section>
              </>
            )}

            {k.management.length > 0 && (
              <>
                <Separator />
                <Section icon={ShieldCheck} title={t("disease.recommendedActions")} color="text-blue-500">
                  <ol className="space-y-2">
                    {k.management.map((a, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/10 text-[10px] font-bold text-blue-500">
                          {i + 1}
                        </span>
                        <span className="text-muted-foreground pt-0.5">{a}</span>
                      </li>
                    ))}
                  </ol>
                </Section>
              </>
            )}

            {k.prevention.length > 0 && (
              <>
                <Separator />
                <Section icon={ShieldCheck} title={t("disease.preventiveMeasures")} color="text-emerald-500">
                  <ul className="space-y-1.5">
                    {k.prevention.map((p, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                        {p}
                      </li>
                    ))}
                  </ul>
                </Section>
              </>
            )}

            <p className="text-[11px] text-muted-foreground">
              {t("disease.guidanceSource")}: {k.source}
            </p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function Section({
  icon: Icon,
  title,
  color,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <Icon className={`h-4 w-4 ${color}`} />
        <h4 className="text-sm font-semibold text-foreground">{title}</h4>
      </div>
      {children}
    </div>
  );
}
