"use client";

import { useMemo } from "react";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import type { H3HexFeature } from "@/types";

interface H3HexLayerProps {
  id: string;
  data: H3HexFeature[];
  pickable?: boolean;
  onHover?: (info: any) => void;
}

function getElevation(confidence: number): number {
  return confidence * 500;
}

function getColor(confidence: number): [number, number, number, number] {
  if (confidence >= 0.7) {
    return [34, 197, 94, 180];
  }
  if (confidence >= 0.4) {
    return [251, 191, 36, 180];
  }
  return [239, 68, 68, 200];
}

export function H3HexLayer({ id, data, pickable = false, onHover }: H3HexLayerProps) {
  return useMemo(
    () =>
      new H3HexagonLayer({
        id,
        data,
        pickable,
        onHover,
        extruded: true,
        wireframe: false,
        elevationScale: 1,
        getHexagon: (d: H3HexFeature) => d.h3_index,
        getFillColor: (d: H3HexFeature) => d.color || getColor(d.confidence),
        getElevation: (d: H3HexFeature) => getElevation(d.confidence),
        elevationRange: [0, 500],
        coverage: 0.95,
        material: {
          ambient: 0.4,
          diffuse: 0.6,
          shininess: 32,
          specularColor: [60, 60, 60],
        },
        _lighting: "pbr" as const,
        transitions: {
          getFillColor: { duration: 800, easing: (t: number) => t * (2 - t) },
          getElevation: { duration: 800, easing: (t: number) => t * (2 - t) },
        },
        updateTriggers: {
          getFillColor: [data],
          getElevation: [data],
        },
      }),
    [data, pickable, onHover, id]
  );
}
