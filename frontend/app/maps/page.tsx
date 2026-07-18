"use client";

import { useState, useCallback, useMemo } from "react";
import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { MapControls } from "@/components/maps/map-controls";
import { MapLegend } from "@/components/maps/map-legend";
import { Skeleton } from "@/components/ui/skeleton";

const MapContainer = dynamic(
  () => import("@/components/maps/map-container").then((mod) => ({ default: mod.MapContainer })),
  { ssr: false, loading: () => <MapSkeleton /> }
);

function MapSkeleton() {
  return (
    <div className="h-full w-full flex items-center justify-center bg-muted/30">
      <div className="text-center space-y-4">
        <Skeleton className="h-64 w-96 rounded-xl" />
        <p className="text-sm text-muted-foreground">Loading map...</p>
      </div>
    </div>
  );
}

export interface LayerVisibility {
  satellite: boolean;
  farmBoundaries: boolean;
  diseaseHeatmap: boolean;
  weather: boolean;
  markets: boolean;
  drone: boolean;
}

export default function MapsPage() {
  const [layers, setLayers] = useState<LayerVisibility>({
    satellite: true,
    farmBoundaries: true,
    diseaseHeatmap: false,
    weather: false,
    markets: false,
    drone: false,
  });

  const toggleLayer = useCallback((key: keyof LayerVisibility) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const layerList = useMemo(
    () => [
      { key: "satellite" as const, label: "Satellite", color: "#3b82f6" },
      { key: "farmBoundaries" as const, label: "Farm Boundaries", color: "#22c55e" },
      { key: "diseaseHeatmap" as const, label: "Disease Heatmap", color: "#ef4444" },
      { key: "weather" as const, label: "Weather", color: "#06b6d4" },
      { key: "markets" as const, label: "Markets", color: "#f59e0b" },
      { key: "drone" as const, label: "Drone", color: "#8b5cf6" },
    ],
    []
  );

  return (
    <DashboardLayout>
      <div className="relative h-[calc(100vh-5rem)] -m-4 lg:-m-6">
        <MapContainer layers={layers} />
        <MapControls layers={layers} onToggle={toggleLayer} />
        <MapLegend layers={layerList} visibility={layers} />
      </div>
    </DashboardLayout>
  );
}
