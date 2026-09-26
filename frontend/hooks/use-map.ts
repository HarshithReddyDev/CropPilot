"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getAgriContext,
  getMapMarkets,
  getMapWeather,
  getViewportMarkets,
  reverseMapPlace,
  searchMapPlaces,
  type AgriContext,
  type MapMarketsQuery,
  type MapViewport,
} from "@/services/map";
import { useMarketsEnabled } from "@/hooks/use-market-intelligence";

/** Rounded coordinate buckets keep React Query keys bounded: nearby cache
 *  entries share per ~1km grid cell instead of per exact coordinate. */
export function coordBucket(v: number): number {
  return Math.round(v * 100) / 100;
}

export function useMapSearch(q: string) {
  const enabled = useMarketsEnabled();
  const query = q.trim();
  return useQuery({
    queryKey: ["map", "search", query],
    queryFn: () => searchMapPlaces(query),
    enabled: enabled && query.length >= 2,
    staleTime: 10 * 60 * 1000,
  });
}

export function useMapReverse(lat: number | null, lng: number | null) {
  const enabled = useMarketsEnabled();
  return useQuery({
    queryKey: ["map", "reverse", lat !== null ? coordBucket(lat) : null, lng !== null ? coordBucket(lng) : null],
    queryFn: () => reverseMapPlace(lat as number, lng as number),
    enabled: enabled && lat !== null && lng !== null,
    staleTime: 60 * 60 * 1000,
    retry: 1,
  });
}

export function useMapMarkets(q: (MapMarketsQuery & { lat: number; lng: number }) | null) {
  const enabled = useMarketsEnabled();
  return useQuery({
    queryKey: [
      "map",
      "markets",
      q ? coordBucket(q.lat) : null,
      q ? coordBucket(q.lng) : null,
      q?.radius_km ?? null,
      q?.district ?? null,
      q?.state ?? null,
      q?.commodity ?? null,
    ],
    queryFn: () => getMapMarkets(q as MapMarketsQuery),
    enabled: enabled && q !== null,
    staleTime: 15 * 60 * 1000,
    retry: 1,
  });
}

export function useViewportMarkets(vp: MapViewport | null, commodity?: string) {
  const enabled = useMarketsEnabled();
  return useQuery({
    queryKey: [
      "map",
      "viewport",
      vp ? coordBucket(vp.min_lat) : null,
      vp ? coordBucket(vp.min_lng) : null,
      vp ? coordBucket(vp.max_lat) : null,
      vp ? coordBucket(vp.max_lng) : null,
      commodity ?? null,
    ],
    queryFn: () => getViewportMarkets(vp as MapViewport, { commodity }),
    enabled: enabled && vp !== null,
    staleTime: 15 * 60 * 1000,
    retry: 1,
  });
}

export function useMapWeather(lat: number | null, lng: number | null) {
  const enabled = useMarketsEnabled();
  return useQuery({
    queryKey: ["map", "weather", lat !== null ? coordBucket(lat) : null, lng !== null ? coordBucket(lng) : null],
    queryFn: () => getMapWeather(lat as number, lng as number),
    enabled: enabled && lat !== null && lng !== null,
    staleTime: 30 * 60 * 1000,
    retry: 1,
  });
}

/** Single aggregated agricultural-intelligence call (soil, rainfall,
 *  crops, suitability, water, disease context, weather). One browser
 *  request; providers fan out server-side with independent degradation. */
export function useAgriContext(
  lat: number | null,
  lng: number | null,
  district?: string | null,
  state?: string | null
) {
  const enabled = useMarketsEnabled();
  return useQuery<AgriContext>({
    queryKey: [
      "map",
      "agri-context",
      lat !== null ? coordBucket(lat) : null,
      lng !== null ? coordBucket(lng) : null,
      district ?? null,
      state ?? null,
    ],
    queryFn: () =>
      getAgriContext(lat as number, lng as number, district ?? undefined, state ?? undefined),
    enabled: enabled && lat !== null && lng !== null,
    staleTime: 60 * 60 * 1000,
    retry: 1,
  });
}
