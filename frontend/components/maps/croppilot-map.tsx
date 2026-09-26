"use client";

import { useEffect, useRef, useState, useCallback, forwardRef, useImperativeHandle } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useTheme } from "next-themes";
import { useTranslation } from "@/lib/i18n";
import type { MapMarket, MapViewport } from "@/services/map";

export const INDIA_VIEW = { lng: 79.5, lat: 22.5, zoom: 4 };

const CARTO_LIGHT = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
const CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

function tileStyle(isDark: boolean): string {
  const override = process.env.NEXT_PUBLIC_MAP_TILE_URL ?? "";
  if (override) return override;
  return isDark ? CARTO_DARK : CARTO_LIGHT;
}

export interface MapSelection {
  lat: number;
  lng: number;
}

export interface ViewRequest {
  lat: number;
  lng: number;
  zoom: number;
  key: number;
}

interface CropPilotMapProps {
  selection: MapSelection | null;
  onSelect: (lat: number, lng: number) => void;
  markets: MapMarket[];
  marketsVisible: boolean;
  selectedMarket: MapMarket | null;
  onMarketSelect: (m: MapMarket | null) => void;
  viewRequest: ViewRequest | null;
  onLocate: () => void;
  locating: boolean;
}

function marketKey(m: MapMarket): string {
  return `${m.state ?? ""}|${m.district ?? ""}|${m.name}`;
}

/** Leaflet-free agricultural map: MapLibre base (CARTO tiles, keyless),
 *  native clustered market markers, branded selected-location marker.
 *  Never renders fake data — every marker comes from props. */
export interface CropPilotMapHandle {
  getBounds: () => MapViewport | null;
  getZoom: () => number;
}

export const CropPilotMap = forwardRef<CropPilotMapHandle, CropPilotMapProps>(function CropPilotMap(
  {
    selection,
    onSelect,
    markets,
    marketsVisible,
    selectedMarket,
    onMarketSelect,
    viewRequest,
    onLocate,
    locating,
  }: CropPilotMapProps,
  ref
) {
  const { t } = useTranslation();
  const { resolvedTheme } = useTheme();
  const wrapRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const onSelectRef = useRef(onSelect);
  const onMarketSelectRef = useRef(onMarketSelect);
  onSelectRef.current = onSelect;
  onMarketSelectRef.current = onMarketSelect;

  const marketsRef = useRef(markets);
  marketsRef.current = markets;
  const layersWiredRef = useRef(false);

  // --- map lifecycle ---
  const [mapFailed, setMapFailed] = useState(false);
  useEffect(() => {
    if (!wrapRef.current || mapRef.current) return;
    let map: maplibregl.Map;
    try {
      map = new maplibregl.Map({
        container: wrapRef.current,
        style: tileStyle(resolvedTheme === "dark"),
        center: [INDIA_VIEW.lng, INDIA_VIEW.lat],
        zoom: INDIA_VIEW.zoom,
        attributionControl: { compact: true },
      });
    } catch {
      // No WebGL (old device, blocked GPU): honest fallback, not a crash.
      setMapFailed(true);
      return;
    }
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    map.on("click", (e) => {
      const feats = map.queryRenderedFeatures(e.point, { layers: ["map-markets-unclustered"] });
      if (feats.length > 0) return; // market clicks handled by layer handler
      onSelectRef.current(
        Math.round(e.lngLat.lat * 10000) / 10000,
        Math.round(e.lngLat.lng * 10000) / 10000
      );
    });
    // Layer click handlers registered once (layers come and go with theme
    // switches; handlers reference live state through refs).
    map.on("click", "map-market-clusters", async (e) => {
      const feats = map.queryRenderedFeatures(e.point, { layers: ["map-market-clusters"] });
      const clusterId = feats[0]?.properties?.cluster_id;
      const srcNow = map.getSource("map-markets") as maplibregl.GeoJSONSource | undefined;
      if (clusterId === undefined || !srcNow?.getClusterExpansionZoom) return;
      const zoom = await srcNow.getClusterExpansionZoom(clusterId as number);
      const coords = (feats[0].geometry as GeoJSON.Point).coordinates as [number, number];
      map.flyTo({ center: coords, zoom, duration: 600 });
    });
    map.on("click", "map-markets-unclustered", (e) => {
      const key = (e.features?.[0]?.properties as { key?: string } | undefined)?.key;
      if (!key) return;
      const found = marketsRef.current.find((m) => marketKey(m) === key) ?? null;
      onMarketSelectRef.current(found);
    });
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- base style follows theme (documented CARTO styles, keyless) ---
  useEffect(() => {
    mapRef.current?.setStyle(tileStyle(resolvedTheme === "dark"));
  }, [resolvedTheme]);

  // --- imperative fly-to ---
  useEffect(() => {
    if (viewRequest && mapRef.current) {
      mapRef.current.flyTo({
        center: [viewRequest.lng, viewRequest.lat],
        zoom: Math.max(mapRef.current.getZoom(), viewRequest.zoom),
        duration: 1200,
      });
    }
  }, [viewRequest]);

  // --- selected-location marker (branded div marker, no image assets) ---
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    markerRef.current?.remove();
    markerRef.current = null;
    if (!selection) return;
    const el = document.createElement("div");
    el.className = "croppilot-selected-marker";
    el.setAttribute("role", "img");
    el.setAttribute("aria-label", t("maps.selectedLocation"));
    el.innerHTML =
      '<svg width="34" height="44" viewBox="0 0 34 44" fill="none" aria-hidden="true">' +
      '<path d="M17 1C8.7 1 2 7.7 2 16c0 11.2 15 27 15 27s15-15.8 15-27C32 7.7 25.3 1 17 1z" fill="#16a34a" stroke="#fff" stroke-width="2"/>' +
      '<circle cx="17" cy="16" r="6" fill="#fff"/>' +
      '<circle cx="17" cy="16" r="3" fill="#16a34a"/></svg>';
    const marker = new maplibregl.Marker({ element: el, anchor: "bottom" })
      .setLngLat([selection.lng, selection.lat])
      .addTo(map);
    markerRef.current = marker;
    return () => {
      marker.remove();
      if (markerRef.current === marker) markerRef.current = null;
    };
  }, [selection, t]);

  // --- market source: clustered GeoJSON, one feature per market ---
  // (layer click handlers live in the map-creation effect; this effect only
  // manages source/layers/data so theme switches rewire without duplicates)
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    // Base-style switches (theme) drop all sources/layers: rewire once.
    if (layersWiredRef.current && !map.getSource("map-markets")) {
      layersWiredRef.current = false;
    }
    const apply = () => {
      const features = marketsVisible
        ? markets.map((m) => ({
            type: "Feature" as const,
            geometry: { type: "Point" as const, coordinates: [m.longitude, m.latitude] },
            properties: { key: marketKey(m) },
          }))
        : [];
      const data = { type: "FeatureCollection" as const, features };
      const src = map.getSource("map-markets") as maplibregl.GeoJSONSource | undefined;
      if (src) {
        src.setData(data);
        return;
      }
      map.addSource("map-markets", {
        type: "geojson",
        data,
        cluster: true,
        clusterMaxZoom: 12,
        clusterRadius: 42,
      });
      map.addLayer({
        id: "map-market-clusters",
        type: "circle",
        source: "map-markets",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": "#b45309",
          "circle-radius": ["step", ["get", "point_count"], 16, 10, 20, 30, 26],
          "circle-opacity": 0.85,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#fff",
        },
      });
      map.addLayer({
        id: "map-market-cluster-count",
        type: "symbol",
        source: "map-markets",
        filter: ["has", "point_count"],
        layout: { "text-field": ["get", "point_count_abbreviated"], "text-size": 12 },
        paint: { "text-color": "#fff" },
      });
      map.addLayer({
        id: "map-markets-unclustered",
        type: "circle",
        source: "map-markets",
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-color": "#d97706",
          "circle-radius": 7,
          "circle-opacity": 0.9,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#fff",
        },
      });
      layersWiredRef.current = true;
    };
    if (layersWiredRef.current) {
      const src = map.getSource("map-markets") as maplibregl.GeoJSONSource | undefined;
      if (src && map.isStyleLoaded()) {
        src.setData({
          type: "FeatureCollection" as const,
          features: marketsVisible
            ? markets.map((m) => ({
                type: "Feature" as const,
                geometry: { type: "Point" as const, coordinates: [m.longitude, m.latitude] },
                properties: { key: marketKey(m) },
              }))
            : [],
        });
      }
      return;
    }
    if (map.isStyleLoaded()) apply();
    else map.once("style.load", apply);
  }, [markets, marketsVisible, resolvedTheme]);

  const resetView = useCallback(() => {
    mapRef.current?.flyTo({ center: [INDIA_VIEW.lng, INDIA_VIEW.lat], zoom: INDIA_VIEW.zoom, duration: 900 });
  }, []);

  const toggleFullscreen = useCallback(() => {
    const el = wrapRef.current?.parentElement;
    if (!el) return;
    if (document.fullscreenElement) void document.exitFullscreen().catch(() => {});
    else void el.requestFullscreen?.().catch(() => {});
  }, []);

  useImperativeHandle(
    ref,
    () => ({
      getBounds: () => {
        const b = mapRef.current?.getBounds();
        if (!b) return null;
        return { min_lat: b.getSouth(), min_lng: b.getWest(), max_lat: b.getNorth(), max_lng: b.getEast() };
      },
      getZoom: () => mapRef.current?.getZoom() ?? INDIA_VIEW.zoom,
    }),
    []
  );

  if (mapFailed) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-muted/30 p-6">
        <p className="max-w-sm text-center text-sm text-muted-foreground" role="alert">
          {t("maps.mapUnavailable")}
        </p>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      <div ref={wrapRef} className="h-full w-full" data-testid="croppilot-map" role="application" aria-label={t("maps.mapLabel")} />
      <div className="absolute left-3 top-3 z-10 flex flex-col gap-2">
        <button
          type="button"
          onClick={onLocate}
          disabled={locating}
          aria-label={t("maps.useMyLocation")}
          title={t("maps.useMyLocation")}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background/90 shadow-sm backdrop-blur transition-colors hover:bg-muted disabled:opacity-50"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <circle cx="12" cy="12" r="3" />
            <path d="M12 2v3M12 19v3M2 12h3M19 12h3" strokeLinecap="round" />
            <circle cx="12" cy="12" r="8" />
          </svg>
        </button>
        <button
          type="button"
          onClick={resetView}
          aria-label={t("maps.resetView")}
          title={t("maps.resetView")}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background/90 shadow-sm backdrop-blur transition-colors hover:bg-muted"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path d="M3 12a9 9 0 1 0 3-6.7M3 4v5h5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <button
          type="button"
          onClick={toggleFullscreen}
          aria-label={t("maps.fullscreen")}
          title={t("maps.fullscreen")}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background/90 shadow-sm backdrop-blur transition-colors hover:bg-muted"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
            <path d="M8 3H5a2 2 0 0 0-2 2v3M16 3h3a2 2 0 0 1 2 2v3M8 21H5a2 2 0 0 1-2-2v-3M16 21h3a2 2 0 0 0 2-2v-3" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </div>
  );
});
