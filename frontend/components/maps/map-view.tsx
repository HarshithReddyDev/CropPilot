"use client";

import { useRef, useMemo, useCallback, useState, useEffect } from "react";
import DeckGL from "@deck.gl/react";
import { MapView as DeckMapView, MapController } from "@deck.gl/core";
import { ScatterplotLayer, PolygonLayer, LineLayer } from "@deck.gl/layers";
import { H3HexagonLayer } from "@deck.gl/geo-layers";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useTelemetrySocket } from "@/hooks/use-telemetry-socket";
import type { LayerVisibility } from "@/app/maps/page";
import type { H3HexFeature } from "@/types";

const INITIAL_VIEW_STATE = {
  longitude: 78.5,
  latitude: 17.5,
  zoom: 7,
  pitch: 0,
  bearing: 0,
};

const mockFarmPolygons = [
  { id: "farm-1", name: "Green Valley Farm", area: 18.5, crop: "Rice", health: 85, polygon: [[78.3, 17.2], [78.6, 17.2], [78.6, 17.5], [78.3, 17.5]], color: [34, 197, 94, 200] as [number, number, number, number] },
  { id: "farm-2", name: "Sunrise Fields", area: 12.2, crop: "Cotton", health: 72, polygon: [[78.8, 17.8], [79.1, 17.8], [79.1, 18.1], [78.8, 18.1]], color: [251, 191, 36, 200] as [number, number, number, number] },
  { id: "farm-3", name: "Riverbend Estate", area: 14.5, crop: "Sugarcane", health: 90, polygon: [[77.8, 16.5], [78.1, 16.5], [78.1, 16.8], [77.8, 16.8]], color: [139, 92, 246, 200] as [number, number, number, number] },
];

// Remove mockH3Hexes constant as it's now handled by useTelemetrySocket

const diseasePoints = Array.from({ length: 60 }, (_, i) => ({
  position: [78.0 + Math.random() * 2.0, 17.0 + Math.random() * 2.5] as [number, number],
  confidence: 0.1 + Math.random() * 0.9,
}));

const marketLocations = [
  { name: "Hyderabad Mandi", position: [78.48, 17.38] as [number, number], volume: 35000, price: 3100 },
  { name: "Warangal Market", position: [79.58, 17.97] as [number, number], volume: 22000, price: 2950 },
  { name: "Nizamabad Mandi", position: [78.10, 18.67] as [number, number], volume: 18000, price: 3050 },
  { name: "Khammam Market", position: [80.15, 17.25] as [number, number], volume: 15000, price: 2880 },
  { name: "Karimnagar Mandi", position: [79.13, 18.44] as [number, number], volume: 12000, price: 2980 },
  { name: "Mahbubnagar Market", position: [77.99, 16.74] as [number, number], volume: 9000, price: 2800 },
  { name: "Nalgonda Market", position: [79.27, 17.06] as [number, number], volume: 8000, price: 2750 },
  { name: "Adilabad Market", position: [78.53, 19.67] as [number, number], volume: 6000, price: 2700 },
];

const weatherStations = [
  { position: [78.5, 17.5] as [number, number], temp: 32, label: "Hyderabad" },
  { position: [79.0, 18.0] as [number, number], temp: 30, label: "Karimnagar" },
  { position: [78.0, 17.0] as [number, number], temp: 34, label: "Mahbubnagar" },
  { position: [79.5, 17.5] as [number, number], temp: 31, label: "Warangal" },
  { position: [78.0, 18.0] as [number, number], temp: 28, label: "Nizamabad" },
];

function getDiseaseColor(confidence: number): [number, number, number, number] {
  if (confidence >= 0.7) return [34, 197, 94, 180];
  if (confidence >= 0.4) return [251, 191, 36, 200];
  return [239, 68, 68, 220];
}

function getPriceColor(price: number): [number, number, number, number] {
  if (price >= 3000) return [239, 68, 68, 200];
  if (price >= 2900) return [251, 191, 36, 200];
  return [34, 197, 94, 200];
}

function getTempColor(temp: number): [number, number, number, number] {
  if (temp >= 33) return [239, 68, 68, 200];
  if (temp >= 30) return [251, 146, 60, 200];
  return [59, 130, 246, 200];
}

interface MapViewProps {
  layers: LayerVisibility;
}

export function MapView({ layers }: MapViewProps) {
  const deckRef = useRef<any>(null);
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [viewState, setViewState] = useState(INITIAL_VIEW_STATE);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [selectedFarm, setSelectedFarm] = useState<any>(null);
  const [selectedMarket, setSelectedMarket] = useState<any>(null);
  
  const hexDataRef = useRef<H3HexFeature[]>([]);
  const layersVisibilityRef = useRef(layers);
  
  useEffect(() => {
    layersVisibilityRef.current = layers;
    updateDeckLayers();
  }, [layers]);

  useEffect(() => {
    if (mapContainer.current && !mapRef.current) {
      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
        zoom: INITIAL_VIEW_STATE.zoom,
        attributionControl: false,
      });
      map.on("load", () => setMapLoaded(true));
      mapRef.current = map;
    }
    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  const syncMapPosition = useCallback((vs: typeof viewState) => {
    mapRef.current?.jumpTo({
      center: [vs.longitude, vs.latitude],
      zoom: vs.zoom,
      pitch: vs.pitch,
      bearing: vs.bearing,
    });
  }, []);

  const generateDeckLayers = useCallback((visibility: LayerVisibility, hexData: H3HexFeature[]) => {
    const result: any[] = [];

    if (visibility.satellite && hexData.length > 0) {
      result.push(
        new H3HexagonLayer({
          id: "h3-hex-layer",
          data: hexData,
          pickable: true,
          extruded: true,
          wireframe: false,
          elevationScale: 1,
          getHexagon: (d: H3HexFeature) => d.h3_index,
          getFillColor: (d: H3HexFeature) => d.color || getDiseaseColor(d.confidence),
          getElevation: (d: H3HexFeature) => d.confidence * 500,
          elevationRange: [0, 500],
          coverage: 0.95,
          material: { ambient: 0.4, diffuse: 0.6, shininess: 32, specularColor: [60, 60, 60] },
          transitions: {
            getFillColor: { duration: 800, easing: (t: number) => t * (2 - t) },
            getElevation: { duration: 800, easing: (t: number) => t * (2 - t) },
          },
        })
      );
    }

    if (visibility.farmBoundaries) {
      result.push(
        new PolygonLayer({
          id: "farm-boundaries",
          data: mockFarmPolygons,
          getPolygon: (d: any) => d.polygon,
          getFillColor: (d: any) => [...d.color.slice(0, 3), 50] as [number, number, number, number],
          getLineColor: (d: any) => d.color,
          getLineWidth: (d: any) => Math.max(2, d.area / 5),
          lineWidthMinPixels: 2,
          lineWidthMaxPixels: 6,
          pickable: true,
          autoHighlight: true,
          highlightColor: [255, 255, 255, 80],
          onClick: (info: any) => { if (info.object) setSelectedFarm(info.object); },
        })
      );
    }

    if (visibility.diseaseHeatmap) {
      result.push(
        new ScatterplotLayer({
          id: "disease-points",
          data: diseasePoints,
          getPosition: (d: any) => d.position,
          getFillColor: (d: any) => getDiseaseColor(d.confidence),
          getRadius: (d: any) => 5 + d.confidence * 15,
          radiusMinPixels: 3,
          radiusMaxPixels: 20,
          opacity: 0.7,
          stroked: false,
        })
      );
    }

    if (visibility.markets) {
      result.push(
        new ScatterplotLayer({
          id: "markets",
          data: marketLocations,
          getPosition: (d: any) => d.position,
          getFillColor: (d: any) => getPriceColor(d.price),
          getRadius: (d: any) => Math.sqrt(d.volume) * 2,
          radiusMinPixels: 8,
          radiusMaxPixels: 40,
          pickable: true,
          autoHighlight: true,
          highlightColor: [255, 255, 255, 150],
          stroked: true,
          getLineColor: [255, 255, 255, 100],
          getLineWidth: 1,
          onClick: (info: any) => { if (info.object) setSelectedMarket(info.object); },
        })
      );
    }

    if (visibility.weather) {
      result.push(
        new ScatterplotLayer({
          id: "weather-stations",
          data: weatherStations,
          getPosition: (d: any) => d.position,
          getFillColor: (d: any) => getTempColor(d.temp),
          getRadius: 15,
          radiusMinPixels: 8,
          radiusMaxPixels: 25,
          pickable: true,
        })
      );
    }

    return result;
  }, []);

  const updateDeckLayers = useCallback(() => {
    if (deckRef.current && deckRef.current.deck) {
      deckRef.current.deck.setProps({
        layers: generateDeckLayers(layersVisibilityRef.current, hexDataRef.current)
      });
    }
  }, [generateDeckLayers]);

  useTelemetrySocket({
    useMockFallback: true,
    onFeaturesUpdate: useCallback((features: H3HexFeature[]) => {
      hexDataRef.current = features;
      updateDeckLayers();
    }, [updateDeckLayers])
  });

  const handleViewStateChange = useCallback(({ viewState: vs }: any) => {
    setViewState(vs);
    syncMapPosition(vs);
  }, [syncMapPosition]);

  return (
    <div className="h-full w-full relative overflow-hidden">
      <div ref={mapContainer} className="absolute inset-0" />
      <div className="absolute inset-0" style={{ pointerEvents: mapLoaded ? "auto" : "none" }}>
        <DeckGL
          ref={deckRef}
          viewState={viewState}
          onViewStateChange={handleViewStateChange}
          controller={{ type: MapController, dragRotate: false }}
          layers={generateDeckLayers(layers, hexDataRef.current)}
          getTooltip={({ object }: any) => {
            if (!object) return null;
            if (object.h3_index) {
              return { html: `<b>Hex:</b> ${object.h3_index.slice(0, 8)}...<br/><b>Crop:</b> ${object.crop_type || "Unknown"}<br/><b>Confidence:</b> ${(object.confidence * 100).toFixed(0)}%` };
            }
            if (object.name) {
              return { html: `<b>${object.name}</b><br/>${object.crop ? `Crop: ${object.crop}` : `Price: ₹${object.price}/qtl`}` };
            }
            return null;
          }}
        />
      </div>

      {selectedFarm && (
        <div className="absolute bottom-6 left-56 z-20 bg-card border border-border/50 rounded-xl p-4 shadow-xl w-60 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-sm">{selectedFarm.name}</h4>
            <button onClick={() => setSelectedFarm(null)} className="text-muted-foreground hover:text-foreground p-0.5"><svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
          </div>
          <div className="space-y-1 text-xs text-muted-foreground">
            <p>Area: <span className="font-medium text-foreground">{selectedFarm.area} ha</span></p>
            <p>Crop: <span className="font-medium text-foreground">{selectedFarm.crop}</span></p>
            <p>Health: <span className="font-medium text-emerald-500">{selectedFarm.health}%</span></p>
          </div>
        </div>
      )}

      {selectedMarket && (
        <div className="absolute bottom-6 left-56 z-20 bg-card border border-border/50 rounded-xl p-4 shadow-xl w-60 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-sm">{selectedMarket.name}</h4>
            <button onClick={() => setSelectedMarket(null)} className="text-muted-foreground hover:text-foreground p-0.5"><svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg></button>
          </div>
          <div className="space-y-1 text-xs text-muted-foreground">
            <p>Volume: <span className="font-medium text-foreground">{selectedMarket.volume.toLocaleString()} qtl</span></p>
            <p>Price: <span className="font-medium text-foreground">&#x20B9;{selectedMarket.price}/qtl</span></p>
          </div>
        </div>
      )}
    </div>
  );
}
