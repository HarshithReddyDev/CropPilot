"use client";

import { useMemo } from "react";
import { ScatterplotLayer } from "@deck.gl/layers";

interface DiseasePoint {
  position: [number, number];
  weight: number;
  confidence: number;
}

function generateDiseasePoints(count: number): DiseasePoint[] {
  return Array.from({ length: count }, () => ({
    position: [
      78.0 + Math.random() * 2.0,
      17.0 + Math.random() * 2.5,
    ] as [number, number],
    weight: Math.random(),
    confidence: 0.1 + Math.random() * 0.9,
  }));
}

function getDiseaseColor(confidence: number): [number, number, number, number] {
  if (confidence >= 0.7) return [34, 197, 94, 180];
  if (confidence >= 0.4) return [251, 191, 36, 200];
  return [239, 68, 68, 220];
}

interface DiseaseHeatmapProps {
  id?: string;
  radiusScale?: number;
  data?: DiseasePoint[];
}

export function DiseaseHeatmap({
  id = "disease-heatmap",
  radiusScale = 1,
  data,
}: DiseaseHeatmapProps) {
  const points = useMemo(() => data || generateDiseasePoints(80), [data]);

  return useMemo(
    () =>
      new ScatterplotLayer({
        id,
        data: points,
        getPosition: (d: DiseasePoint) => d.position,
        getFillColor: (d: DiseasePoint) => getDiseaseColor(d.confidence),
        getRadius: (d: DiseasePoint) => 4 + d.confidence * 20 * radiusScale,
        radiusMinPixels: 3,
        radiusMaxPixels: 30,
        opacity: 0.65,
        stroked: false,
        _subLayerProps: {
          circles: { radiusScale: 1 },
        },
        transitions: {
          getRadius: { duration: 600, easing: (t: number) => t * (2 - t) },
          getFillColor: { duration: 600, easing: (t: number) => t * (2 - t) },
        },
        updateTriggers: {
          getRadius: [points, radiusScale],
          getFillColor: [points],
        },
      }),
    [points, radiusScale, id]
  );
}
