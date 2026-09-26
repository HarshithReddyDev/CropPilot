"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Bug, Leaf, AlertTriangle, RotateCcw } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useTranslation } from "@/lib/i18n";
import { CameraUpload } from "@/components/disease/camera-upload";
import { DragDropUpload } from "@/components/disease/drag-drop-upload";
import { DiseaseResultCard } from "@/components/disease/disease-result-card";
import { AnalysisDetails } from "@/components/disease/analysis-details";
import { TreatmentCard } from "@/components/disease/treatment-card";
import { DetectionHistory, type SessionHistoryEntry } from "@/components/disease/detection-history";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { ApiError } from "@/services/api";
import {
  analyzeDisease,
  dataUrlToFile,
  getDiseaseCapabilities,
  isModelFailure,
  isNoCoverage,
  type DiseaseAnalysis,
  type DiseaseCapabilities,
} from "@/services/disease";

type DetectionStatus = "idle" | "processing" | "complete" | "error";

function errorKey(status: number, data: unknown): string {
  const code =
    typeof data === "object" && data !== null && "detail" in data
      ? (data as { detail?: unknown }).detail
      : null;
  const inner =
    typeof code === "object" && code !== null && "code" in code
      ? String((code as { code?: unknown }).code ?? "")
      : "";
  if (status === 0) return "disease.errNetwork";
  if (status === 400) {
    if (inner === "IMAGE_TOO_LARGE") return "disease.errTooLarge";
    if (inner === "IMAGE_POOR_QUALITY") return "disease.errPoorQuality";
    if (inner === "UNSUPPORTED_CROP") return "disease.errUnsupportedCrop";
    return "disease.errInvalid";
  }
  if (status === 502) return "disease.errModelFailure";
  if (status === 503) {
    if (inner === "NO_VALID_MODEL") return "disease.errNoCoverage";
    return "disease.errModelFailure";
  }
  return "disease.errServer";
}

export default function DiseaseDetectionPage() {
  const { t, locale } = useTranslation();
  const [status, setStatus] = useState<DetectionStatus>("idle");
  const [analysis, setAnalysis] = useState<DiseaseAnalysis | null>(null);
  const [preview, setPreview] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [cropHint, setCropHint] = useState<string>("");
  const [capabilities, setCapabilities] = useState<DiseaseCapabilities | null>(null);
  const [capsOffline, setCapsOffline] = useState(false);
  const [history, setHistory] = useState<SessionHistoryEntry[]>([]);
  // Full results kept in memory only (images never persisted).
  const [resultCache, setResultCache] = useState<Record<string, DiseaseAnalysis>>({});
  // Last submitted file, kept in memory so the farmer can re-analyze with a
  // manually selected crop without re-uploading. Never persisted.
  const [lastFile, setLastFile] = useState<{ file: File; preview: string } | null>(null);
  // In-flight guard: one analysis at a time, so a single interaction can
  // never produce two requests (and two history entries).
  const inflight = useRef(false);

  useEffect(() => {
    let cancelled = false;
    getDiseaseCapabilities()
      .then((c) => {
        if (!cancelled) setCapabilities(c);
      })
      .catch(() => {
        if (!cancelled) setCapsOffline(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const runAnalysis = useCallback(
    async (file: File, previewUrl: string) => {
      if (inflight.current) return;
      inflight.current = true;
      setStatus("processing");
      setAnalysis(null);
      setPreview(previewUrl);
      setError(null);
      setLastFile({ file, preview: previewUrl });
      try {
        const result = await analyzeDisease(file, {
          cropHint: cropHint || undefined,
          language: locale,
        });
        setAnalysis(result);
        setResultCache((c) => ({ ...c, [result.request_id]: result }));
        const top = result.findings[0];
        // A raw model class is NOT crop identification: when the crop is
        // unknown and the outcome is uncertain, history records "no
        // diagnosis" rather than the top raw class (e.g. a tomato label
        // on a photo that may not be tomato at all).
        const cropUnconfirmed =
          result.crop.source === "unknown" && result.status === "uncertain";
        const entry: SessionHistoryEntry = {
          id: result.request_id,
          date: new Date().toISOString(),
          crop: result.crop.name,
          cropStatus: result.crop.status,
          disease: top && !cropUnconfirmed ? top.display_name : null,
          band: top && !cropUnconfirmed ? top.confidence_band : null,
          status: result.status,
          reason: result.reason_code,
        };
        // Idempotent write: one history entry per request_id. A retry that
        // somehow reuses an id updates the row instead of duplicating it.
        setHistory((h) => [entry, ...h.filter((e) => e.id !== entry.id)].slice(0, 20));
        setStatus("complete");
      } catch (e) {
        const key =
          e instanceof ApiError ? errorKey(e.status, e.data) : "disease.errServer";
        setError(t(key));
        setStatus("error");
      } finally {
        inflight.current = false;
      }
    },
    [cropHint, locale, t]
  );

  const handleSelectHistory = useCallback(
    (entry: SessionHistoryEntry) => {
      const cached = resultCache[entry.id];
      if (!cached) return;
      setAnalysis(cached);
      setPreview(undefined);
      setError(null);
      setStatus("complete");
    },
    [resultCache]
  );

  const handleReset = useCallback(() => {
    if (inflight.current) return;
    setStatus("idle");
    setAnalysis(null);
    setPreview(undefined);
    setError(null);
    setCropHint("");
    setLastFile(null);
  }, []);

  // "Analyze again" after manually selecting a crop: reuses the in-memory
  // file, sends the new user-provided hint. The hint is routing context,
  // never model evidence.
  const handleAnalyzeAgain = useCallback(() => {
    if (lastFile && !inflight.current) void runAnalysis(lastFile.file, lastFile.preview);
  }, [lastFile, runAnalysis]);

  const hasFinding =
    analysis !== null &&
    (analysis.status === "diagnosed" || analysis.status === "probable") &&
    analysis.findings.length > 0;
  const noCoverage = analysis !== null && isNoCoverage(analysis);
  const modelFailure = analysis !== null && isModelFailure(analysis);
  const poorImage =
    analysis !== null &&
    (analysis.status === "insufficient_image" || analysis.reason_code === "POOR_IMAGE_QUALITY");
  const lowConfidence =
    analysis !== null &&
    analysis.status === "uncertain" &&
    !noCoverage &&
    !modelFailure;
  // Model class outputs are only agronomically plausible alternatives when
  // the crop context is established. With an unknown crop they are raw
  // outputs (transparency section), never "Possible alternatives".
  const cropKnown = analysis !== null && analysis.crop.source !== "unknown";
  const showGuidance =
    hasFinding && analysis !== null && analysis.knowledge.length > 0;
  const supported = capabilities?.crops_with_production_specialist ?? [];
  const taxonomyCrops = capabilities?.taxonomy_crops ?? [];

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-7xl space-y-6" aria-live="polite">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              {t("disease.title")}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {t("disease.subtitle")}
            </p>
          </div>
          {status !== "idle" && (
            <button
              onClick={handleReset}
              aria-label={t("disease.newDetection")}
              className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
              {t("disease.newDetection")}
            </button>
          )}
        </motion.div>

        {capsOffline && (
          <div className="flex items-center gap-2 rounded-lg bg-amber-500/10 px-4 py-3 text-sm text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
            {t("disease.capabilitiesOffline")}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-5">
          <div className="space-y-6 lg:col-span-2">
            {status === "idle" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <div className="glass-card p-5">
                  <label
                    htmlFor="disease-crop-hint"
                    className="mb-2 block text-sm font-medium text-foreground"
                  >
                    {t("disease.cropHintLabel")}
                  </label>
                  <select
                    id="disease-crop-hint"
                    value={cropHint}
                    onChange={(e) => setCropHint(e.target.value)}
                    className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-primary"
                  >
                    <option value="">{t("disease.cropHintAuto")}</option>
                    {taxonomyCrops.map((c) => (
                      <option key={c} value={c}>
                        {c}
                        {supported.includes(c) ? "" : ` (${t("disease.coverageBadge")})`}
                      </option>
                    ))}
                  </select>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {t("disease.supportedCropsNote")}:{" "}
                    {supported.length > 0 ? supported.join(", ") : "—"}
                  </p>
                </div>
                <CameraUpload
                  onCapture={(dataUrl) =>
                    runAnalysis(dataUrlToFile(dataUrl), dataUrl)
                  }
                />
                <DragDropUpload
                  onFile={(file, previewUrl) => runAnalysis(file, previewUrl)}
                />
              </motion.div>
            )}

            {status === "processing" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-4"
              >
                <div className="glass-card p-6">
                  <div className="flex flex-col items-center gap-4 py-8">
                    <div className="relative">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        className="flex h-16 w-16 items-center justify-center"
                      >
                        <Leaf className="h-8 w-8 text-primary" aria-hidden="true" />
                      </motion.div>
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className="absolute -inset-2 rounded-full border-2 border-dashed border-primary/30"
                      />
                    </div>
                    <p className="text-sm font-medium text-foreground">
                      {t("disease.stageAnalyzing")}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {t("disease.analyzingBody")}
                    </p>
                  </div>
                </div>
                <Skeleton className="h-32 rounded-xl" />
                <Skeleton className="h-48 rounded-xl" />
              </motion.div>
            )}

            {(status === "complete" || status === "error") && analysis && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                {preview && (
                  <div className="glass-card overflow-hidden">
                    <img
                      src={preview}
                      alt={t("disease.uploadedPhoto")}
                      className="h-48 w-full object-cover"
                    />
                  </div>
                )}
                <AnalysisDetails result={analysis} />
              </motion.div>
            )}

            {status === "error" && !analysis && (
              <div className="glass-card space-y-3 p-6 text-center">
                <AlertTriangle className="mx-auto h-8 w-8 text-red-500" aria-hidden="true" />
                <p className="text-sm font-medium text-foreground">
                  {error ?? t("disease.errServer")}
                </p>
                <p className="text-xs text-muted-foreground">
                  {t("disease.analyzeAnotherHint")}
                </p>
              </div>
            )}
          </div>

          <div className="space-y-6 lg:col-span-3">
            {status === "idle" && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-muted-foreground/20 py-16"
              >
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
                  <Bug className="h-10 w-10 text-muted-foreground/50" aria-hidden="true" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">
                  {t("disease.readyTitle")}
                </h3>
                <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
                  {t("disease.readyBody")}
                </p>
                {capabilities && (
                  <div className="mt-6 max-w-md px-4">
                    <p className="mb-2 text-center text-xs font-medium text-foreground">
                      {t("disease.coverageTitle")}
                    </p>
                    <p className="text-center text-xs text-muted-foreground">
                      {t("disease.coverageBody", {
                        count: capabilities.production_models.length,
                      })}
                    </p>
                    {supported.length > 0 && (
                      <div className="mt-3 flex flex-wrap justify-center gap-2">
                        {supported.map((c) => (
                          <Badge key={c} variant="secondary" className="text-[10px]">
                            {c}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )}

            {status === "processing" && (
              <div className="space-y-6">
                <div className="glass-card space-y-2 p-6">
                  <p className="text-sm font-medium text-foreground">
                    {t("disease.stepsTitle")}
                  </p>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    <li>{t("disease.stepUpload")}</li>
                    <li>{t("disease.stepQuality")}</li>
                    <li>{t("disease.stepRouting")}</li>
                    <li>{t("disease.stepAnalysis")}</li>
                    <li>{t("disease.stepVerify")}</li>
                  </ul>
                </div>
                <Skeleton className="h-64 rounded-xl" />
                <Skeleton className="h-48 rounded-xl" />
                <Skeleton className="h-32 rounded-xl" />
              </div>
            )}

            {status === "complete" && analysis && hasFinding && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <DiseaseResultCard result={analysis} imageUrl={preview} />
                {showGuidance && <TreatmentCard knowledge={analysis.knowledge} />}
              </motion.div>
            )}

            {status === "complete" && analysis && !hasFinding && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-card space-y-4 p-6"
              >
                <div className="flex items-center gap-3">
                  <AlertTriangle
                    className="h-6 w-6 text-amber-500"
                    aria-hidden="true"
                    aria-label={t("disease.analysisIncomplete")}
                  />
                  <h3 className="text-base font-semibold text-foreground">
                    {noCoverage
                      ? t("disease.noCoverageTitle")
                      : modelFailure
                        ? t("disease.temporaryAnalysisFailure")
                        : poorImage
                          ? t("disease.photoNeedsImprovement")
                          : t("disease.lowConfidenceTitle")}
                  </h3>
                </div>

                {noCoverage && (
                  <Badge variant="outline" className="text-[11px]">
                    {t("disease.coverageBadge")}
                  </Badge>
                )}
                {modelFailure && (
                  <Badge variant="outline" className="text-[11px]">
                    {t("disease.serviceBadge")}
                  </Badge>
                )}

                <p className="text-sm font-medium text-foreground">
                  {t("disease.noVerifiedDiagnosis")}
                </p>
                <p className="text-sm text-muted-foreground">
                  {noCoverage
                    ? analysis.crop.status === "unknown"
                      ? t("disease.cropUnknownNoModel")
                      : t("disease.noSpecialistAvailable")
                    : modelFailure
                      ? t("disease.modelFailureBody")
                      : lowConfidence && !cropKnown
                        ? t("disease.cropUnknownWeakEvidence")
                        : lowConfidence
                          ? t("disease.lowConfidenceBody")
                          : analysis.next_action}
                </p>

                {lowConfidence && !cropKnown && (
                  <div data-testid="unknown-crop-row" className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">{t("disease.cropLabel")}:</span>
                    <span className="font-medium text-foreground">
                      {analysis.crop.name ?? t("disease.cropNotIdentified")}
                    </span>
                  </div>
                )}

                {cropKnown && (noCoverage || lowConfidence) && analysis.alternatives.length > 0 && (
                  <div>
                    <p className="mb-2 text-sm font-medium text-foreground">
                      {t("disease.possibleCauses")}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {analysis.alternatives.map((a) => (
                        <Badge key={a.disease_id} variant="secondary">
                          {a.display_name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <p className="mb-2 text-sm font-medium text-foreground">
                    {t("disease.whyLabel")}
                  </p>
                  <p className="rounded-lg bg-muted/50 px-4 py-3 text-sm text-muted-foreground">
                    {lowConfidence && !cropKnown
                      ? t("disease.unknownCropWhy")
                      : analysis.next_action}
                  </p>
                </div>

                <div>
                  <p className="mb-2 text-sm font-medium text-foreground">
                    {t("disease.whatToDoLabel")}
                  </p>
                  <div className="flex flex-wrap items-center gap-2">
                    {(noCoverage || lowConfidence) && (
                      <>
                        <label
                          htmlFor="disease-recrop"
                          className="text-sm text-muted-foreground"
                        >
                          {t("disease.selectCropPrompt")}
                        </label>
                        <select
                          id="disease-recrop"
                          value={cropHint}
                          onChange={(e) => setCropHint(e.target.value)}
                          className="rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-primary"
                        >
                          <option value="">{t("disease.cropHintAuto")}</option>
                          {taxonomyCrops.map((c) => (
                            <option key={c} value={c}>
                              {c}
                            </option>
                          ))}
                        </select>
                        <button
                          onClick={handleAnalyzeAgain}
                          disabled={!lastFile || !cropHint}
                          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity disabled:opacity-50"
                        >
                          {t("disease.analyzeAgain")}
                        </button>
                      </>
                    )}
                    {modelFailure && (
                      <button
                        onClick={handleAnalyzeAgain}
                        disabled={!lastFile}
                        className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity disabled:opacity-50"
                      >
                        {t("disease.retryAnalysis")}
                      </button>
                    )}
                    <button
                      onClick={handleReset}
                      className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                    >
                      {t("disease.analyzeAnotherPhoto")}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            <DetectionHistory entries={history} onSelect={handleSelectHistory} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
