"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bug,
  Leaf,
  AlertTriangle,
  FlaskConical,
  ShieldCheck,
  ListChecks,
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { CameraUpload } from "@/components/disease/camera-upload";
import { DragDropUpload } from "@/components/disease/drag-drop-upload";
import { DiseaseResultCard } from "@/components/disease/disease-result-card";
import { ConfidenceGauge } from "@/components/disease/confidence-gauge";
import { TreatmentCard } from "@/components/disease/treatment-card";
import { DetectionHistory } from "@/components/disease/detection-history";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type DetectionStatus = "idle" | "processing" | "complete" | "error";

interface DetectionResult {
  disease: string;
  confidence: number;
  severity: "low" | "moderate" | "high" | "critical";
  boundingBoxes: { x: number; y: number; width: number; height: number; label: string }[];
  imageUrl?: string;
}

interface TreatmentData {
  disease: string;
  symptoms: string[];
  actions: string[];
  preventive: string[];
  products: { name: string; dosage: string }[];
}

interface HistoryEntry {
  id: string;
  date: string;
  crop: string;
  disease: string;
  confidence: number;
  severity: "low" | "moderate" | "high" | "critical";
  status: "resolved" | "treatment" | "pending";
}

const DISEASE_DATABASE: Record<string, { treatment: TreatmentData; severity: DetectionResult["severity"] }> = {
  "Rice Blast": {
    severity: "high",
    treatment: {
      disease: "Rice Blast",
      symptoms: [
        "Diamond-shaped lesions with gray centers on leaves",
        "White to grey-green lesions with dark borders",
        "Neck blast causes panicle to break and fall",
        "Infected nodes turn black and rot",
      ],
      actions: [
        "Remove and destroy infected plant debris immediately",
        "Apply Tricyclazole 75% WP at 0.6g per liter of water",
        "Spray Carbendazim 50% WP at 1g per liter of water",
        "Maintain proper spacing for air circulation",
        "Avoid excessive nitrogen fertilization",
      ],
      preventive: [
        "Use resistant varieties like IR64, Pusa Basmati 1",
        "Treat seeds with hot water (54°C for 10 minutes)",
        "Practice crop rotation with legumes",
        "Maintain proper field drainage",
        "Monitor crop weekly during humid conditions",
      ],
      products: [
        { name: "Tricyclazole 75% WP", dosage: "0.6g/L water" },
        { name: "Carbendazim 50% WP", dosage: "1g/L water" },
        { name: "Mancozeb 75% WP", dosage: "2.5g/L water" },
      ],
    },
  },
  "Wheat Rust": {
    severity: "high",
    treatment: {
      disease: "Wheat Rust (Brown/Leaf Rust)",
      symptoms: [
        "Small orange-brown pustules on leaves in linear arrangement",
        "Chlorotic patches surrounding pustules",
        "Premature leaf senescence",
        "Reduced grain filling and yield loss",
      ],
      actions: [
        "Apply Propiconazole 25% EC at 1ml per liter of water",
        "Spray Tebuconazole 250 EC at 1ml per liter of water",
        "Repeat spray after 15 days if symptoms persist",
        "Remove volunteer wheat plants from fields",
        "Avoid wheat-on-wheat continuous cropping",
      ],
      preventive: [
        "Grow rust-resistant varieties like HD 2967, PBW 550",
        "Early sowing to escape disease pressure",
        "Avoid dense planting - maintain recommended spacing",
        "Balanced fertilization - avoid excess nitrogen",
        "Monitor crop regularly during March-April",
      ],
      products: [
        { name: "Propiconazole 25% EC", dosage: "1ml/L water" },
        { name: "Tebuconazole 250 EC", dosage: "1ml/L water" },
        { name: "Zineb 75% WP", dosage: "2g/L water" },
      ],
    },
  },
  "Cotton Leaf Curl": {
    severity: "critical",
    treatment: {
      disease: "Cotton Leaf Curl Virus",
      symptoms: [
        "Leaf curling upward or downward with thickened veins",
        "Stunted plant growth and shortened internodes",
        "Vein darkening and formation of leaf-like enations",
        "Reduced boll formation and poor fiber quality",
      ],
      actions: [
        "Control whitefly vector with Imidacloprid 17.8% SL at 0.5ml/L",
        "Remove and destroy infected plants immediately",
        "Apply Neem oil 1% as botanical insecticide",
        "Install yellow sticky traps at 12-15 per acre",
        "Maintain weed-free field to reduce vector habitat",
      ],
      preventive: [
        "Use resistant hybrids like RCH 659 BGII, NCS 2778 BGII",
        "Avoid intercropping with okra, tomato, tobacco",
        "Sow during recommended window to avoid peak whitefly",
        "Border crop with maize or sorghum as barrier",
        "Apply Imidacloprid seed treatment before sowing",
      ],
      products: [
        { name: "Imidacloprid 17.8% SL", dosage: "0.5ml/L water" },
        { name: "Neem Oil 1% EC", dosage: "5ml/L water" },
        { name: "Yellow Sticky Traps", dosage: "12-15 per acre" },
      ],
    },
  },
  "Early Blight": {
    severity: "moderate",
    treatment: {
      disease: "Early Blight (Tomato/Potato)",
      symptoms: [
        "Dark brown spots with concentric rings on older leaves",
        "Yellowing and defoliation starting from lower leaves",
        "Lesions on stems and fruits near calyx end",
        "Target board pattern on infected tubers",
      ],
      actions: [
        "Remove and destroy infected lower leaves",
        "Apply Chlorothalonil 75% WP at 2g per liter of water",
        "Spray Mancozeb 75% WP at 2g per liter of water",
        "Ensure proper plant spacing for air circulation",
        "Apply mulching to reduce soil splash",
      ],
      preventive: [
        "Use certified disease-free seeds and tubers",
        "Practice 3-year crop rotation",
        "Avoid overhead irrigation - use drip irrigation",
        "Apply copper-based fungicides preventively",
        "Maintain proper plant nutrition with adequate potassium",
      ],
      products: [
        { name: "Chlorothalonil 75% WP", dosage: "2g/L water" },
        { name: "Mancozeb 75% WP", dosage: "2g/L water" },
        { name: "Copper Oxychloride 50% WP", dosage: "3g/L water" },
      ],
    },
  },
};

const MOCK_CROPS = ["Rice", "Wheat", "Cotton", "Tomato", "Potato", "Maize"];

const MOCK_HISTORY: HistoryEntry[] = [
  { id: "1", date: "2026-07-10T08:30:00Z", crop: "Rice", disease: "Rice Blast", confidence: 92, severity: "high", status: "treatment" },
  { id: "2", date: "2026-07-05T10:15:00Z", crop: "Wheat", disease: "Wheat Rust", confidence: 78, severity: "moderate", status: "resolved" },
  { id: "3", date: "2026-06-28T14:00:00Z", crop: "Cotton", disease: "Cotton Leaf Curl", confidence: 88, severity: "critical", status: "treatment" },
  { id: "4", date: "2026-06-20T09:45:00Z", crop: "Tomato", disease: "Early Blight", confidence: 85, severity: "moderate", status: "resolved" },
  { id: "5", date: "2026-06-12T11:30:00Z", crop: "Rice", disease: "Rice Blast", confidence: 65, severity: "low", status: "resolved" },
  { id: "6", date: "2026-06-05T16:00:00Z", crop: "Potato", disease: "Early Blight", confidence: 95, severity: "high", status: "pending" },
];

export default function DiseaseDetectionPage() {
  const [status, setStatus] = useState<DetectionStatus>("idle");
  const [result, setResult] = useState<DetectionResult | null>(null);
  const [treatment, setTreatment] = useState<TreatmentData | null>(null);

  const simulateDetection = useCallback(async (imageUrl: string) => {
    setStatus("processing");
    setResult(null);
    setTreatment(null);

    await new Promise((resolve) => setTimeout(resolve, 2000 + Math.random() * 1000));

    const diseaseNames = Object.keys(DISEASE_DATABASE);
    const randomDisease = diseaseNames[Math.floor(Math.random() * diseaseNames.length)];
    const db = DISEASE_DATABASE[randomDisease];
    const confidence = 75 + Math.floor(Math.random() * 20);

    const detectionResult: DetectionResult = {
      disease: randomDisease,
      confidence: confidence / 100,
      severity: db.severity,
      boundingBoxes: [
        { x: 0.15, y: 0.2, width: 0.35, height: 0.45, label: randomDisease },
      ],
      imageUrl,
    };

    setResult(detectionResult);
    setTreatment(db.treatment);
    setStatus("complete");
  }, []);

  const handleSelectHistory = useCallback((entry: HistoryEntry) => {
    const db = DISEASE_DATABASE[entry.disease];
    if (!db) return;

    setResult({
      disease: entry.disease,
      confidence: entry.confidence / 100,
      severity: entry.severity,
      boundingBoxes: [
        { x: 0.15, y: 0.2, width: 0.35, height: 0.45, label: entry.disease },
      ],
      imageUrl: undefined,
    });
    setTreatment(db.treatment);
    setStatus("complete");
  }, []);

  const handleReset = useCallback(() => {
    setStatus("idle");
    setResult(null);
    setTreatment(null);
  }, []);

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-7xl space-y-6">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Disease Detection
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Upload or capture crop images for AI-powered disease diagnosis
            </p>
          </div>
          {status !== "idle" && (
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              New Detection
            </button>
          )}
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-5">
          <div className="space-y-6 lg:col-span-2">
            {status === "idle" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <CameraUpload onCapture={simulateDetection} />
                <DragDropUpload
                  onFile={(_file, preview) => simulateDetection(preview)}
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
                        <Leaf className="h-8 w-8 text-primary" />
                      </motion.div>
                      <motion.div
                        animate={{ scale: [1, 1.2, 1] }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className="absolute -inset-2 rounded-full border-2 border-dashed border-primary/30"
                      />
                    </div>
                    <p className="text-sm font-medium text-foreground">
                      Analyzing your crop image...
                    </p>
                    <p className="text-xs text-muted-foreground">
                      AI is scanning for disease patterns
                    </p>
                  </div>
                </div>
                <Skeleton className="h-32 rounded-xl" />
                <Skeleton className="h-48 rounded-xl" />
              </motion.div>
            )}

            {status === "complete" && result && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <DiseaseResultCard result={result} />
                <div className="flex justify-center">
                  <ConfidenceGauge
                    value={result.confidence * 100}
                    label="AI Confidence"
                  />
                </div>
              </motion.div>
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
                  <Bug className="h-10 w-10 text-muted-foreground/50" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-foreground">
                  Ready to Diagnose
                </h3>
                <p className="mt-2 max-w-sm text-center text-sm text-muted-foreground">
                  Upload or capture a photo of the affected crop to get instant
                  AI-powered disease detection and treatment recommendations
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {Object.keys(DISEASE_DATABASE).map((d) => (
                    <Badge key={d} variant="secondary" className="text-[10px]">
                      {d}
                    </Badge>
                  ))}
                </div>
              </motion.div>
            )}

            {status === "processing" && (
              <div className="space-y-6">
                <Skeleton className="h-64 rounded-xl" />
                <Skeleton className="h-48 rounded-xl" />
                <Skeleton className="h-32 rounded-xl" />
              </div>
            )}

            {status === "complete" && treatment && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <TreatmentCard data={treatment} />
              </motion.div>
            )}

            <DetectionHistory entries={MOCK_HISTORY} onSelect={handleSelectHistory} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
