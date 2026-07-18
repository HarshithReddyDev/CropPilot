"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import type { LayerVisibility } from "@/app/maps/page";

const MapView = dynamic(
  () => import("@/components/maps/map-view").then((mod) => ({ default: mod.MapView })),
  { ssr: false, loading: () => <MapSkeleton /> }
);

function MapSkeleton() {
  return (
    <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-muted/50 to-background">
      <div className="text-center space-y-4">
        <div className="relative mx-auto w-64 h-48 rounded-xl overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-primary/10 animate-pulse" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="space-y-2">
              <Skeleton className="h-3 w-48 mx-auto" />
              <Skeleton className="h-3 w-32 mx-auto" />
              <Skeleton className="h-3 w-40 mx-auto" />
            </div>
          </div>
        </div>
        <div className="flex items-center justify-center gap-2">
          <div className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "0ms" }} />
          <div className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "150ms" }} />
          <div className="h-2 w-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
        <p className="text-sm text-muted-foreground">Loading map view...</p>
      </div>
    </div>
  );
}

interface MapContainerProps {
  layers: LayerVisibility;
}

export function MapContainer({ layers }: MapContainerProps) {
  const hasMapboxToken =
    typeof process !== "undefined" &&
    (process.env.NEXT_PUBLIC_MAPBOX_TOKEN || "").length > 0;

  if (!hasMapboxToken) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-muted/50 to-background">
        <div className="text-center max-w-md px-6">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-amber-100 dark:bg-amber-950/30 flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold mb-2">Mapbox Token Required</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Set <code className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">NEXT_PUBLIC_MAPBOX_TOKEN</code> in your environment variables to enable the map view.
          </p>
          <p className="text-xs text-muted-foreground">
            Get a free token at mapbox.com
          </p>
        </div>
      </div>
    );
  }

  return <MapView layers={layers} />;
}
