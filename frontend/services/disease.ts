import { apiPost, apiGet } from "./api";

export type DiagnosisStatus =
  | "diagnosed"
  | "probable"
  | "uncertain"
  | "insufficient_image"
  | "unsupported_crop"
  | "error";

export type ReasonCode =
  | "NO_ELIGIBLE_SPECIALIST"
  | "NO_VERIFIED_MODEL_FOR_CROP"
  | "MODEL_LOAD_FAILED"
  | "MODEL_INFERENCE_FAILED"
  | "INFERENCE_TIMEOUT"
  | "LOW_CONFIDENCE"
  | "SPECIALIST_DISAGREEMENT"
  | "POOR_IMAGE_QUALITY"
  | "IMAGE_INVALID"
  | "IMAGE_TOO_LARGE"
  | "IMAGE_POOR_QUALITY"
  | "NO_VALID_MODEL"
  | "UNSUPPORTED_CROP"
  | "SYSTEM_ERROR"
  | "VLM_UNAVAILABLE"
  | "KNOWLEDGE_UNAVAILABLE";

export type ConfidenceBand = "high" | "medium" | "low" | "unverified" | "unknown";

export type CropStatus = "known" | "unknown" | "unsupported";
export type CropSource = "user" | "model" | "unknown";

export interface AnalysisRegion {
  kind: "full" | "center_crop" | "crop" | "detector";
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  score: number | null;
  source: string;
}

export interface AnalysisFinding {
  disease_id: string;
  display_name: string;
  region: AnalysisRegion;
  raw_score: number | null;
  calibrated_score: number | null;
  score_type: "raw_model_score" | "calibrated";
  confidence_band: ConfidenceBand;
  evidence_level: string;
  model_ids: string[];
  agreement_count: number;
  field_validation: string;
  notes: string | null;
}

export interface EvidenceItem {
  model_id: string;
  license_status: string;
  evidence_level: string;
  field_validation: string;
  metric_context: string | null;
  research_only: boolean;
}

export interface KnowledgeItem {
  disease_id: string;
  title: string;
  symptoms: string[];
  similar_conditions: string[];
  management: string[];
  prevention: string[];
  source: string;
  language: string;
}

export interface DiseaseAnalysis {
  request_id: string;
  status: DiagnosisStatus;
  reason_code: ReasonCode | null;
  crop: {
    name: string | null;
    confidence_band: ConfidenceBand;
    source: CropSource;
    status: CropStatus;
  };
  image_quality: {
    status: "good" | "acceptable" | "poor" | "rejected";
    score: number;
    reasons: string[];
    width: number;
    height: number;
    format: string;
  };
  findings: AnalysisFinding[];
  alternatives: AnalysisFinding[];
  routing: {
    routing_mode: string;
    specialists_considered: string[];
    specialists_run: string[];
    crop_hint: string | null;
    crop_status: CropStatus;
    eligible_specialists: string[];
    excluded_specialists: Record<string, string>;
  };
  evidence: EvidenceItem[];
  knowledge: KnowledgeItem[];
  citations: string[];
  next_action: string;
  pipeline: {
    routing_mode: string;
    specialists_considered: string[];
    specialists_run: string[];
    specialist_latencies_ms: Record<string, number>;
    quality_latency_ms: number;
    router_latency_ms: number;
    fusion_latency_ms: number;
    vlm_latency_ms: number;
    total_latency_ms: number;
    vlm_used: boolean;
    rag_used: boolean;
  };
  error_code: string | null;
}

export interface DiseaseCapabilities {
  enabled: boolean;
  production_models: string[];
  research_models: string[];
  crops_with_production_specialist: string[];
  taxonomy_crops: string[];
  vlm_configured: boolean;
  research_mode: boolean;
  routing_modes: string[];
}

const NO_COVERAGE_REASONS: ReadonlySet<string> = new Set([
  "NO_ELIGIBLE_SPECIALIST",
  "NO_VERIFIED_MODEL_FOR_CROP",
  "NO_VALID_MODEL",
  "UNSUPPORTED_CROP",
]);

const MODEL_FAILURE_REASONS: ReadonlySet<string> = new Set([
  "MODEL_LOAD_FAILED",
  "MODEL_INFERENCE_FAILED",
  "INFERENCE_TIMEOUT",
]);

/** Routing correctly found no runnable model: a coverage gap, not a bug. */
export function isNoCoverage(r: DiseaseAnalysis): boolean {
  if (r.status === "unsupported_crop") return true;
  return r.reason_code !== null && NO_COVERAGE_REASONS.has(r.reason_code);
}

/** A real specialist existed but loading or inference failed: retryable. */
export function isModelFailure(r: DiseaseAnalysis): boolean {
  if (r.status === "error") return true;
  return r.reason_code !== null && MODEL_FAILURE_REASONS.has(r.reason_code);
}

/** POST /api/v1/disease/analyze — multipart upload, real model inference. */export async function analyzeDisease(
  file: File | Blob,
  opts?: { cropHint?: string; language?: string }
): Promise<DiseaseAnalysis> {
  const form = new FormData();
  const payload =
    file instanceof File ? file : new File([file], "capture.jpg", { type: "image/jpeg" });
  form.append("file", payload);
  if (opts?.cropHint) form.append("crop_hint", opts.cropHint);
  form.append("language", opts?.language ?? "en");
  return apiPost<DiseaseAnalysis>("/api/v1/disease/analyze", form, {
    headers: {},
  });
}

export async function getDiseaseCapabilities(): Promise<DiseaseCapabilities> {
  return apiGet<DiseaseCapabilities>("/api/v1/disease/capabilities");
}

export async function listDiseaseModels(): Promise<{
  registry_version: string;
  models: Array<Record<string, unknown>>;
}> {
  return apiGet("/api/v1/disease/models");
}

/** Convert a camera data-URL to a File for upload. */
export function dataUrlToFile(dataUrl: string, name = "capture.jpg"): File {
  const [header, base64] = dataUrl.split(",");
  const mime = header.match(/data:(.*?);/)?.[1] ?? "image/jpeg";
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  return new File([bytes], name, { type: mime });
}
