"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ListChecks,
  ShieldCheck,
  FlaskConical,
  ChevronRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface TreatmentData {
  disease: string;
  symptoms: string[];
  actions: string[];
  preventive: string[];
  products: { name: string; dosage: string }[];
}

interface TreatmentCardProps {
  data: TreatmentData;
}

export function TreatmentCard({ data }: TreatmentCardProps) {
  return (
    <motion.div
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
              Treatment Recommendation
            </h3>
            <p className="text-xs text-muted-foreground">
              For: <span className="font-medium text-foreground">{data.disease}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-5 p-5">
        <Section icon={ListChecks} title="Symptoms" color="text-rose-500">
          <ul className="space-y-1.5">
            {data.symptoms.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-400" />
                {s}
              </li>
            ))}
          </ul>
        </Section>

        <Separator />

        <Section icon={ShieldCheck} title="Recommended Actions" color="text-blue-500">
          <ol className="space-y-2">
            {data.actions.map((a, i) => (
              <li key={i} className="flex items-start gap-3 text-sm">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-500/10 text-[10px] font-bold text-blue-500">
                  {i + 1}
                </span>
                <span className="text-muted-foreground pt-0.5">{a}</span>
              </li>
            ))}
          </ol>
        </Section>

        <Separator />

        <Section icon={ShieldCheck} title="Preventive Measures" color="text-emerald-500">
          <ul className="space-y-1.5">
            {data.preventive.map((p, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-400" />
                {p}
              </li>
            ))}
          </ul>
        </Section>

        {data.products.length > 0 && (
          <>
            <Separator />
            <Section icon={FlaskConical} title="Recommended Products" color="text-violet-500">
              <div className="space-y-2">
                {data.products.map((p, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/30 px-3 py-2.5"
                  >
                    <span className="text-sm font-medium text-foreground">{p.name}</span>
                    <Badge variant="outline" className="text-[10px]">
                      {p.dosage}
                    </Badge>
                  </div>
                ))}
              </div>
            </Section>
          </>
        )}
      </div>
    </motion.div>
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
