"use client";

import { Microscope } from "lucide-react";
import { useTranslation } from "@/lib/i18n";
import type { DiseaseAnalysis } from "@/services/disease";

/**
 * Collapsed technical transparency panel. Everything shown is backend
 * metadata: routing mode, crop identification state, specialists, evidence
 * levels, calibration and validation status. Never a diagnosis.
 */
export function AnalysisDetails({ result }: { result: DiseaseAnalysis }) {
  const { t } = useTranslation();

  const cropLabel =
    result.crop.name ??
    (result.crop.status === "unsupported"
      ? t("disease.cropUnsupported")
      : t("disease.cropNotIdentified"));
  const cropSource =
    result.crop.source === "user"
      ? t("disease.cropSourceUser")
      : t("disease.cropSourceUnknown");
  const specialists =
    result.routing.specialists_run.length > 0
      ? result.routing.specialists_run
      : result.routing.eligible_specialists;
  const calibration =
    result.findings.length > 0 && result.findings[0].score_type === "calibrated"
      ? result.findings[0].score_type
      : t("disease.calibrationUnavailable");
  const vlm = result.pipeline.vlm_used
    ? t("disease.vlmUsed")
    : t("disease.vlmNotConfigured");

  return (
    <details className="glass-card space-y-3 p-5">
      <summary className="flex cursor-pointer items-center gap-2 text-sm font-medium text-foreground">
        <Microscope className="h-4 w-4" aria-hidden="true" />
        {t("disease.evidenceTitle")}
      </summary>
      <dl className="space-y-1.5 text-xs text-muted-foreground">
        <div className="flex justify-between gap-4">
          <dt>{t("disease.imageQuality")}</dt>
          <dd className="text-foreground">
            {result.image_quality.status} ({Math.round(result.image_quality.score * 100)}%)
          </dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>{t("disease.cropIdentification")}</dt>
          <dd className="text-end text-foreground">{cropLabel}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>{t("disease.cropSource")}</dt>
          <dd className="text-end text-foreground">{cropSource}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>{t("disease.routingLabel")}</dt>
          <dd className="text-foreground">{result.routing.routing_mode}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>{t("disease.specialistsLabel")}</dt>
          <dd className="text-end text-foreground">
            {specialists.length > 0 ? specialists.join(", ") : t("disease.specialistsNone")}
          </dd>
        </div>
        {result.evidence.map((e) => (
          <div key={e.model_id} className="flex justify-between gap-4">
            <dt className="break-all">{e.model_id}</dt>
            <dd className="shrink-0 text-foreground">
              {e.evidence_level} · {e.license_status}
              {e.research_only ? ` · ${t("disease.researchBadge")}` : ""}
            </dd>
          </div>
        ))}
        {[ ...result.findings, ...result.alternatives ].length > 0 && (
          <div className="space-y-1 pt-1">
            <dt className="font-medium text-foreground">{t("disease.modelOutputs")}</dt>
            {[ ...result.findings, ...result.alternatives ].map((f) => (
              <div key={f.disease_id} className="flex justify-between gap-4">
                <dt className="break-all">{f.display_name}</dt>
                <dd className="shrink-0 text-foreground">
                  {t("disease.rawScoreLabel")}:{" "}
                  {f.raw_score !== null ? f.raw_score.toFixed(3) : "—"}
                </dd>
              </div>
            ))}
            <p className="text-[11px] text-muted-foreground">
              {t("disease.modelOutputsInterpretation")}
            </p>
          </div>
        )}
        <div className="flex justify-between gap-4">
          <dt>{t("disease.calibrationLabel")}</dt>
          <dd className="text-end text-foreground">{calibration}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>{t("disease.fieldValidation")}</dt>
          <dd className="text-foreground">
            {result.findings[0] ? result.findings[0].field_validation : t("disease.notVerified")}
          </dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>{t("disease.vlmLabel")}</dt>
          <dd className="text-foreground">{vlm}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt>{t("disease.latencyLabel")}</dt>
          <dd className="text-foreground">
            {Math.round(result.pipeline.total_latency_ms)} ms
          </dd>
        </div>
      </dl>
    </details>
  );
}
