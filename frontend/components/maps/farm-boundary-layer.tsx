"use client";

import { useMemo } from "react";
import { PolygonLayer } from "@deck.gl/layers";

interface FarmBoundary {
  id: string;
  name: string;
  area: number;
  crop: string;
  health: number;
  polygon: [number, number][];
  color: [number, number, number, number];
}

const mockFarms: FarmBoundary[] = [
  {
    id: "farm-1",
    name: "Green Valley Farm",
    area: 18.5,
    crop: "Rice",
    health: 85,
    polygon: [[78.3, 17.2], [78.6, 17.2], [78.6, 17.5], [78.3, 17.5]],
    color: [34, 197, 94, 200],
  },
  {
    id: "farm-2",
    name: "Sunrise Fields",
    area: 12.2,
    crop: "Cotton",
    health: 72,
    polygon: [[78.8, 17.8], [79.1, 17.8], [79.1, 18.1], [78.8, 18.1]],
    color: [251, 191, 36, 200],
  },
  {
    id: "farm-3",
    name: "Riverbend Estate",
    area: 14.5,
    crop: "Sugarcane",
    health: 90,
    polygon: [[77.8, 16.5], [78.1, 16.5], [78.1, 16.8], [77.8, 16.8]],
    color: [139, 92, 246, 200],
  },
  {
    id: "farm-4",
    name: "Golden Grains Farm",
    area: 22.0,
    crop: "Wheat",
    health: 68,
    polygon: [[79.2, 17.0], [79.5, 17.0], [79.5, 17.3], [79.2, 17.3]],
    color: [6, 182, 212, 200],
  },
  {
    id: "farm-5",
    name: "Harvest Moon Estate",
    area: 8.8,
    crop: "Maize",
    health: 78,
    polygon: [[77.5, 18.2], [77.7, 18.2], [77.7, 18.4], [77.5, 18.4]],
    color: [236, 72, 153, 200],
  },
];

interface FarmBoundaryLayerProps {
  onFarmClick?: (farm: FarmBoundary) => void;
}

export function FarmBoundaryLayer({ onFarmClick }: FarmBoundaryLayerProps) {
  return useMemo(
    () =>
      new PolygonLayer({
        id: "farm-boundary-layer",
        data: mockFarms,
        getPolygon: (d: FarmBoundary) => d.polygon,
        getFillColor: (d: FarmBoundary) => [...d.color.slice(0, 3), 50] as [number, number, number, number],
        getLineColor: (d: FarmBoundary) => d.color,
        getLineWidth: (d: FarmBoundary) => Math.max(2, d.area / 4),
        lineWidthMinPixels: 2,
        lineWidthMaxPixels: 8,
        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 255, 80],
        stroked: true,
        extruded: false,
        wireframe: true,
        material: {
          ambient: 0.5,
          diffuse: 0.6,
          shininess: 24,
        },
        onClick: (info: any) => {
          if (info.object && onFarmClick) {
            onFarmClick(info.object);
          }
        },
        updateTriggers: {
          getFillColor: [mockFarms],
          getLineColor: [mockFarms],
        },
      }),
    [onFarmClick]
  );
}

export type { FarmBoundary };
