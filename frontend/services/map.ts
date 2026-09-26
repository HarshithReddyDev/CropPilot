import { apiFetch } from "./api";

/** Strict map API types. Coordinates are numbers; everything else may be
 *  null. No `any` for map API data. */

export interface MapLocation {
  latitude: number;
  longitude: number;
  locality?: string | null;
  district?: string | null;
  state?: string | null;
  country?: string | null;
}

export interface MapSearchResult {
  type: "state" | "district" | "market" | "place" | string;
  name: string;
  district?: string | null;
  state?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  source: string;
}

export interface MapReverseResult extends MapLocation {
  display_name?: string | null;
  postcode?: string | null;
  source?: string | null;
}

export interface MapMarketPrice {
  commodity?: string | null;
  variety?: string | null;
  grade?: string | null;
  modal_price?: number | null;
  price_per_unit?: string | null;
  arrival_date?: string | null;
  arrivals?: number | null;
  source?: string | null;
}

export interface MapMarket {
  name: string;
  district?: string | null;
  state?: string | null;
  latitude: number;
  longitude: number;
  coordinate_source: string;
  distance_km?: number | null;
  latest?: MapMarketPrice | null;
}

export interface MapMarketsResponse {
  markets: MapMarket[];
  unmapped_count: number;
  radius_km?: number | null;
  district?: string | null;
  state?: string | null;
}

export interface MapWeather {
  latitude: number;
  longitude: number;
  h3_index: string;
  temperature_c?: number | null;
  feels_like_c?: number | null;
  humidity_pct?: number | null;
  rain_mm?: number | null;
  wind_speed?: number | null;
  wind_deg?: number | null;
  condition?: string | null;
  recorded_at?: string | null;
  fetched_now: boolean;
  source: string;
}

export type SectionStatus = "available" | "unavailable";

export interface Section<T> {
  status: SectionStatus;
  data: T | null;
  source?: string | null;
  reason?: string | null;
}

export interface SoilData {
  texture?: string | null;
  ph?: number | null;
  ph_uncertainty?: number | null;
  organic_carbon_gkg?: number | null;
  organic_carbon_pct?: number | null;
  sand_pct?: number | null;
  silt_pct?: number | null;
  clay_pct?: number | null;
  cec_cmolkg?: number | null;
  nitrogen_gkg?: number | null;
}

export interface RainfallData {
  today_mm?: number | null;
  last_7d_mm?: number | null;
  last_7d_coverage?: string | null;
  month_mm?: number | null;
  month_coverage?: string | null;
  season_mm?: number | null;
  season_label?: string | null;
  season_coverage?: string | null;
}

export interface CommonCrop {
  commodity: string;
  arrival_share?: number | null;
  observations?: number | null;
}

export interface SuitabilityEstimate {
  crop: string;
  suitability_band: "High" | "Moderate" | "Low" | string;
  factors: string[];
  limitations: string[];
  note?: string | null;
}

export interface DiseaseRisk {
  crop: string;
  diseases: Array<{
    disease_id: string;
    display_name: string;
    priority?: string | null;
    has_guidance?: boolean | null;
  }>;
}

export interface AgriSnapshot {
  common_crops?: string[] | null;
  soil?: { texture?: string | null; ph?: number | null } | null;
  season_rain_mm?: number | null;
  season_label?: string | null;
  disease_names?: string[] | null;
}

export interface AgriContext {
  location: {
    latitude: number;
    longitude: number;
    locality?: string | null;
    district?: string | null;
    state?: string | null;
    country?: string | null;
  };
  snapshot?: AgriSnapshot | null;
  weather?: Section<{
    temperature_c?: number | null;
    feels_like_c?: number | null;
    humidity_pct?: number | null;
    rain_mm?: number | null;
    wind_speed?: number | null;
    wind_deg?: number | null;
    condition?: string | null;
    recorded_at?: string | null;
    h3_index?: string | null;
    fetched_now?: boolean | null;
    source?: string | null;
  }> | null;
  rainfall?: Section<RainfallData> | null;
  soil?: Section<SoilData> & {
    source_detail?: string | null;
    license?: string | null;
    resolution_m?: number | null;
    depth?: string | null;
    mode?: string | null;
    mode_note?: string | null;
  } | null;
  crops?: Section<{
    common?: CommonCrop[] | null;
    window_days?: number | null;
    district?: string | null;
    state?: string | null;
    interpretation?: string | null;
  }> & { data_year?: string | null; from_cache?: boolean | null } | null;
  suitability?: Section<{ estimates?: SuitabilityEstimate[] | null; disclaimer?: string | null }> & {
    mode?: string | null;
    mode_note?: string | null;
  } | null;
  water?: Section<null> & {
    reason_note?: string | null;
    groundwater?: Section<null> & { mode?: string | null; mode_note?: string | null } | null;
    reservoirs?: Section<null> & { mode?: string | null; mode_note?: string | null } | null;
  } | null;
  disease_context?: Section<{ crop_risks?: DiseaseRisk[] | null; interpretation?: string | null }> & {
    mode?: string | null;
  } | null;
  sources?: string[] | null;
}

export interface DataSourceInfo {
  source_id: string;
  name: string;
  provider: string;
  type: string;
  license: string;
  coverage: string;
  granularity: string;
  refresh_frequency: string;
  enabled: boolean;
  notes: string;
}

export async function getAgriContext(
  lat: number,
  lng: number,
  district?: string,
  state?: string
): Promise<AgriContext> {
  const params: Record<string, string | number> = { lat, lng };
  if (district) params.district = district;
  if (state) params.state = state;
  return apiFetch<AgriContext>("/api/v1/map/agricultural-context", { params });
}

export async function getMapDataSources(): Promise<{ sources: DataSourceInfo[] }> {
  return apiFetch<{ sources: DataSourceInfo[] }>("/api/v1/map/data-sources");
}

export interface MapAssistantContext {
  page: "map";
  location: {
    latitude: number;
    longitude: number;
    locality?: string | null;
    district?: string | null;
    state?: string | null;
  };
  active_layers: string[];
  selected_market?: string | null;
  soil?: { texture?: string | null; ph?: number | null } | null;
  crops?: string[] | null;
  weather?: { temperature_c?: number | null; humidity_pct?: number | null } | null;
  rainfall?: { season_mm?: number | null; season_label?: string | null } | null;
  saved_at: string;
}

const MAP_CTX_KEY = "croppilot-map-context";

export async function searchMapPlaces(q: string): Promise<MapSearchResult[]> {
  return apiFetch<MapSearchResult[]>("/api/v1/map/search", {
    params: { q },
  });
}

export async function reverseMapPlace(lat: number, lng: number): Promise<MapReverseResult> {
  return apiFetch<MapReverseResult>("/api/v1/map/reverse", {
    params: { lat, lng },
  });
}

export interface MapMarketsQuery {
  lat?: number;
  lng?: number;
  radius_km?: number;
  state?: string;
  district?: string;
  commodity?: string;
  limit?: number;
}

export async function getMapMarkets(q: MapMarketsQuery): Promise<MapMarketsResponse> {
  const params: Record<string, string | number> = {};
  if (q.lat !== undefined && q.lng !== undefined) {
    params.lat = q.lat;
    params.lng = q.lng;
  }
  if (q.radius_km !== undefined) params.radius_km = q.radius_km;
  if (q.state) params.state = q.state;
  if (q.district) params.district = q.district;
  if (q.commodity) params.commodity = q.commodity;
  if (q.limit !== undefined) params.limit = q.limit;
  return apiFetch<MapMarketsResponse>("/api/v1/map/markets", { params });
}

export interface MapViewport {
  min_lat: number;
  min_lng: number;
  max_lat: number;
  max_lng: number;
}

export async function getViewportMarkets(
  vp: MapViewport,
  opts?: { commodity?: string; limit?: number }
): Promise<MapMarketsResponse> {
  return apiFetch<MapMarketsResponse>("/api/v1/map/viewport-markets", {
    params: {
      min_lat: vp.min_lat,
      min_lng: vp.min_lng,
      max_lat: vp.max_lat,
      max_lng: vp.max_lng,
      ...(opts?.commodity ? { commodity: opts.commodity } : {}),
      ...(opts?.limit !== undefined ? { limit: opts.limit } : {}),
    },
  });
}

export async function getMapWeather(lat: number, lng: number): Promise<MapWeather> {
  return apiFetch<MapWeather>("/api/v1/map/weather", { params: { lat, lng } });
}

/** Persist map context for the AI Assistant handoff (session-scoped,
 *  consumed once by the assistant page, never persisted server-side). */
export function saveMapAssistantContext(ctx: Omit<MapAssistantContext, "saved_at" | "page">): void {
  try {
    const payload: MapAssistantContext = {
      ...ctx,
      page: "map",
      saved_at: new Date().toISOString(),
    };
    sessionStorage.setItem(MAP_CTX_KEY, JSON.stringify(payload));
  } catch {
    // storage unavailable: the assistant link still works without context
  }
}

/** Read (and clear) a fresh map context. Returns null when absent/stale. */
export function takeMapAssistantContext(maxAgeMs = 15 * 60 * 1000): MapAssistantContext | null {
  try {
    const raw = sessionStorage.getItem(MAP_CTX_KEY);
    sessionStorage.removeItem(MAP_CTX_KEY);
    if (!raw) return null;
    const ctx = JSON.parse(raw) as MapAssistantContext;
    if (!ctx || ctx.page !== "map" || !ctx.location) return null;
    if (Date.now() - new Date(ctx.saved_at).getTime() > maxAgeMs) return null;
    return ctx;
  } catch {
    return null;
  }
}
