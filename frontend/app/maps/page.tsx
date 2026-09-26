"use client";

import { useState, useCallback, useRef, useMemo, useEffect } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useTranslation } from "@/lib/i18n";
import { MapSearch } from "@/components/maps/map-search";
import { LocationPanel } from "@/components/maps/location-panel";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useAgriContext,
  useMapMarkets,
  useMapReverse,
  useMapWeather,
  useViewportMarkets,
} from "@/hooks/use-map";
import {
  saveMapAssistantContext,
  type MapMarket,
  type MapSearchResult,
  type MapViewport,
} from "@/services/map";
import type { CropPilotMapHandle, ViewRequest } from "@/components/maps/croppilot-map";

const CropPilotMap = dynamic(
  () =>
    import("@/components/maps/croppilot-map").then((mod) => ({ default: mod.CropPilotMap })),
  { ssr: false, loading: () => <MapSkeleton /> }
);

function MapSkeleton() {
  const { t } = useTranslation();
  return (
    <div className="flex h-full w-full items-center justify-center bg-muted/30">
      <div className="space-y-4 text-center">
        <Skeleton className="mx-auto h-64 w-96 rounded-xl" />
        <p className="text-sm text-muted-foreground">{t("maps.loading")}</p>
      </div>
    </div>
  );
}

function readUrl(): { lat: number | null; lng: number | null; zoom: number | null } {
  if (typeof window === "undefined") return { lat: null, lng: null, zoom: null };
  const p = new URLSearchParams(window.location.search);
  const num = (k: string) => {
    const v = p.get(k);
    if (v === null) return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };
  const lat = num("lat");
  const lng = num("lng");
  if (lat === null || lng === null || Math.abs(lat) > 90 || Math.abs(lng) > 180) {
    return { lat: null, lng: null, zoom: null };
  }
  return { lat, lng, zoom: num("zoom") };
}

type GeoError = "denied" | "unavailable" | "timeout" | "unsupported" | null;

export default function MapsPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const mapRef = useRef<CropPilotMapHandle>(null);
  // SSR-safe: server and first client render agree (no selection); the URL
  // is applied in a post-hydration effect so shared links never cause a
  // hydration mismatch.
  const [selection, setSelection] = useState<{ lat: number; lng: number } | null>(null);
  useEffect(() => {
    const u = readUrl();
    if (u.lat !== null && u.lng !== null) setSelection({ lat: u.lat, lng: u.lng });
  }, []);
  const [viewRequest, setViewRequest] = useState<ViewRequest | null>(null);
  const [marketsVisible, setMarketsVisible] = useState(true);
  const [commodity, setCommodity] = useState("");
  const [mode, setMode] = useState<"nearby" | "viewport">("nearby");
  const [viewport, setViewport] = useState<MapViewport | null>(null);
  const [selectedMarket, setSelectedMarket] = useState<MapMarket | null>(null);
  const [geoError, setGeoError] = useState<GeoError>(null);
  const [locating, setLocating] = useState(false);
  const [sheetExpanded, setSheetExpanded] = useState(false);

  const syncUrl = useCallback((lat: number, lng: number) => {
    const zoom = mapRef.current?.getZoom();
    const p = new URLSearchParams();
    p.set("lat", String(lat));
    p.set("lng", String(lng));
    if (zoom !== undefined) p.set("zoom", String(Math.round(zoom * 10) / 10));
    router.replace(`/maps?${p.toString()}`, { scroll: false });
  }, [router]);

  const handleSelect = useCallback(
    (lat: number, lng: number) => {
      setSelection({ lat, lng });
      setSelectedMarket(null);
      setMode("nearby");
      setViewport(null);
      setSheetExpanded(false);
      syncUrl(lat, lng);
    },
    [syncUrl]
  );

  const flyTo = useCallback((lat: number, lng: number, zoom = 10) => {
    setViewRequest({ lat, lng, zoom, key: Date.now() });
  }, []);

  const handleSearchPick = useCallback(
    (r: MapSearchResult) => {
      if (r.latitude == null || r.longitude == null) return;
      handleSelect(r.latitude, r.longitude);
      flyTo(r.latitude, r.longitude, r.type === "state" ? 7 : 10);
    },
    [handleSelect, flyTo]
  );

  const handleLocate = useCallback(() => {
    if (typeof navigator === "undefined" || !navigator.geolocation) {
      setGeoError("unsupported");
      return;
    }
    setLocating(true);
    setGeoError(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        const lat = Math.round(pos.coords.latitude * 10000) / 10000;
        const lng = Math.round(pos.coords.longitude * 10000) / 10000;
        handleSelect(lat, lng);
        flyTo(lat, lng, 11);
      },
      (err) => {
        setLocating(false);
        setGeoError(
          err.code === err.PERMISSION_DENIED
            ? "denied"
            : err.code === err.POSITION_UNAVAILABLE
              ? "unavailable"
              : err.code === err.TIMEOUT
                ? "timeout"
                : "unavailable"
        );
      },
      { timeout: 12000, maximumAge: 60000 }
    );
  }, [handleSelect, flyTo]);

  const reverse = useMapReverse(selection?.lat ?? null, selection?.lng ?? null);
  const district = reverse.data?.district ?? null;
  const state = reverse.data?.state ?? null;
  // Weather stays on its own fast query (Open-Meteo, 30-min stale); the
  // aggregate also carries weather for context, but the panel must not
  // wait on slow providers (soil) for the temperature card.
  const weather = useMapWeather(selection?.lat ?? null, selection?.lng ?? null);
  const agri = useAgriContext(
    selection?.lat ?? null,
    selection?.lng ?? null,
    district,
    state
  );

  const marketsQuery = useMapMarkets(
    selection && mode === "nearby"
      ? {
          lat: selection.lat,
          lng: selection.lng,
          radius_km: 50,
          district: district ?? undefined,
          state: state ?? undefined,
          commodity: commodity || undefined,
          limit: 10,
        }
      : null
  );
  const viewportQuery = useViewportMarkets(
    mode === "viewport" ? viewport : null,
    commodity || undefined
  );
  const weatherSummary = useMemo(() => {
    const w = agri.data?.weather?.data;
    if (!w || w.temperature_c == null) return null;
    return { temperature_c: w.temperature_c, humidity_pct: w.humidity_pct ?? null };
  }, [agri.data]);
  const marketsData = mode === "viewport" ? viewportQuery.data ?? null : marketsQuery.data ?? null;
  const marketsLoading = mode === "viewport" ? viewportQuery.isFetching : marketsQuery.isFetching;
  const marketsError = mode === "viewport" ? viewportQuery.isError : marketsQuery.isError;

  const handleSearchArea = useCallback(() => {
    const b = mapRef.current?.getBounds();
    if (!b) return;
    setMode("viewport");
    setViewport(b);
    setSelectedMarket(null);
  }, []);

  const handleMarketSelect = useCallback(
    (m: MapMarket | null) => {
      setSelectedMarket(m);
      if (m) flyTo(m.latitude, m.longitude, 10);
    },
    [flyTo]
  );

  const handleAskAssistant = useCallback(() => {
    if (selection) {
      const snap = agri.data?.snapshot ?? null;
      const rainD = agri.data?.rainfall?.data ?? null;
      saveMapAssistantContext({
        location: {
          latitude: selection.lat,
          longitude: selection.lng,
          locality: reverse.data?.locality ?? null,
          district,
          state,
        },
        active_layers: marketsVisible ? ["markets"] : [],
        selected_market: selectedMarket?.name ?? null,
        soil: snap?.soil
          ? { texture: snap.soil.texture ?? null, ph: snap.soil.ph ?? null }
          : null,
        crops: snap?.common_crops ?? null,
        weather: weatherSummary,
        rainfall: rainD
          ? { season_mm: rainD.season_mm ?? null, season_label: rainD.season_label ?? null }
          : null,
      });
    }
    router.push("/ai-assistant");
  }, [selection, reverse.data, district, state, marketsVisible, selectedMarket, agri.data, weatherSummary, router]);

  const geoErrorText = useMemo(() => {
    switch (geoError) {
      case "denied":
        return t("maps.geoDenied");
      case "unavailable":
        return t("maps.geoUnavailable");
      case "timeout":
        return t("maps.geoTimeout");
      case "unsupported":
        return t("maps.geoUnsupported");
      default:
        return null;
    }
  }, [geoError, t]);

  return (
    <DashboardLayout>
      <div className="relative -m-4 h-[calc(100vh-5rem)] lg:-m-6">
        {/* Map layer */}
        <div className="absolute inset-0">
          <CropPilotMap
            ref={mapRef}
            selection={selection}
            onSelect={handleSelect}
            markets={marketsData?.markets ?? []}
            marketsVisible={marketsVisible}
            selectedMarket={selectedMarket}
            onMarketSelect={setSelectedMarket}
            viewRequest={viewRequest}
            onLocate={handleLocate}
            locating={locating}
          />
        </div>

        {/* Search (floating, top) */}
        <div className="absolute left-3 right-3 top-3 z-20 sm:left-16 sm:right-auto sm:w-96">
          <MapSearch onPick={handleSearchPick} />
          {geoErrorText && (
            <p className="mt-2 rounded-lg border border-border bg-background/95 px-3 py-2 text-xs text-muted-foreground backdrop-blur" role="alert">
              {geoErrorText}
            </p>
          )}
        </div>

        {/* Layer toggle */}
        <div className="absolute bottom-6 right-3 z-10 sm:bottom-8">
          <button
            type="button"
            onClick={() => setMarketsVisible((v) => !v)}
            aria-pressed={marketsVisible}
            aria-label={t("maps.toggleMarkets")}
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium shadow-sm backdrop-blur transition-colors ${
              marketsVisible
                ? "border-primary bg-primary/10 text-foreground"
                : "border-border bg-background/90 text-muted-foreground hover:bg-muted"
            }`}
          >
            <span
              className={`h-2.5 w-2.5 rounded-full ${marketsVisible ? "bg-amber-600" : "bg-muted-foreground/40"}`}
              aria-hidden="true"
            />
            {t("maps.markets")}
          </button>
        </div>

        {/* Insights: desktop sidebar / mobile bottom sheet */}
        {selection ? (
          <aside
            aria-label={t("maps.locationInsights")}
            className={`absolute z-20 flex flex-col rounded-t-2xl border border-border bg-background/98 shadow-xl backdrop-blur-xl transition-all
              inset-x-0 bottom-0 max-h-[42vh]
              lg:inset-x-auto lg:bottom-4 lg:right-4 lg:top-4 lg:w-[380px] lg:rounded-2xl lg:max-h-none ${
              sheetExpanded ? "max-h-[85vh]" : ""
            }`}
          >
            <div className="flex items-center justify-between gap-2 border-b border-border/50 px-4 py-2 lg:hidden">
              <button
                type="button"
                onClick={() => setSheetExpanded((v) => !v)}
                aria-expanded={sheetExpanded}
                aria-label={t(sheetExpanded ? "maps.collapseSheet" : "maps.expandSheet")}
                className="mx-auto flex h-8 w-full items-center justify-center"
              >
                <span className="h-1 w-12 rounded-full bg-muted-foreground/30" aria-hidden="true" />
              </button>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-4">
              <LocationPanel
                lat={selection.lat}
                lng={selection.lng}
                reverse={reverse.data ?? null}
                reverseLoading={reverse.isFetching}
                reverseError={reverse.isError}
                weather={weather.data ?? null}
                weatherLoading={weather.isFetching}
                weatherError={weather.isError}
                agri={agri.data ?? null}
                agriLoading={agri.isFetching}
                agriError={agri.isError}
                markets={marketsData}
                marketsLoading={marketsLoading}
                marketsError={marketsError}
                commodity={commodity}
                onCommodity={setCommodity}
                onSearchArea={handleSearchArea}
                searchAreaLoading={viewportQuery.isFetching}
                selectedMarket={selectedMarket}
                onMarketSelect={handleMarketSelect}
                onAskAssistant={handleAskAssistant}
              />
            </div>
          </aside>
        ) : (
          <div className="pointer-events-none absolute inset-x-0 bottom-6 z-10 hidden justify-center lg:flex">
            <p className="rounded-full border border-border bg-background/90 px-4 py-2 text-xs text-muted-foreground shadow-sm backdrop-blur">
              {t("maps.pickHint")}
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
