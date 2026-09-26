"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getMarketCommodities,
  getMarketDistricts,
  getMarketGrades,
  getMarketMarkets,
  getMarketStates,
  getMarketVarieties,
  getMarketsComparison,
  getMarketsHistory,
  getMarketsLatest,
  getMarketsOverview,
  type ComparisonQuery,
  type HistoryQuery,
  type LatestQuery,
  type MetaScope,
} from "@/services/markets";
import { useAuthStore } from "@/stores/auth-store";
import { useAuthReady } from "@/hooks/use-auth-ready";

const META_STALE = 6 * 60 * 60 * 1000;

// Local development only: when set, the backend serves a deterministic
// development identity without credentials, so market queries run without
// a token. Never set this in production builds.
const DEV_AUTH_BYPASS =
  process.env.NEXT_PUBLIC_DEV_AUTH_BYPASS === "true";

/**
 * Protected market queries may only run once auth state is initialized
 * and a bearer token is present. Firing them earlier sends unauthenticated
 * requests whose failures, after retries, leave the page stuck showing a
 * backend-outage message that only a filter change would clear.
 */
export function useMarketsEnabled(): boolean {
  const ready = useAuthReady();
  const token = useAuthStore((s) => s.token);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (DEV_AUTH_BYPASS) return ready;
  return ready && isAuthenticated && token !== null;
}

export function useMarketsLatest(params: LatestQuery) {
  const enabled = useMarketsEnabled();
  return useQuery({
    queryKey: ["markets", "latest", params],
    queryFn: () => getMarketsLatest(params),
    enabled,
  });
}

export function useMarketsHistory(params: HistoryQuery | null) {
  const enabled =
    useMarketsEnabled() && params !== null && params.commodity !== "";
  return useQuery({
    queryKey: ["markets", "history", params],
    queryFn: () => getMarketsHistory(params as HistoryQuery),
    enabled,
  });
}

export function useMarketsComparison(params: ComparisonQuery | null) {
  const enabled =
    useMarketsEnabled() && params !== null && params.commodity !== "";
  return useQuery({
    queryKey: ["markets", "comparison", params],
    queryFn: () => getMarketsComparison(params as ComparisonQuery),
    enabled,
  });
}

export function useMarketsOverview(state?: string) {
  const enabled = useMarketsEnabled();
  return useQuery({
    queryKey: ["markets", "overview", state ?? "national"],
    queryFn: () => getMarketsOverview(state),
    staleTime: 30 * 60 * 1000,
    enabled,
  });
}

export function useMarketStates() {
  const enabled = useMarketsEnabled();
  return useQuery({
    queryKey: ["markets", "meta", "states"],
    queryFn: getMarketStates,
    staleTime: META_STALE,
    enabled,
  });
}

export function useMarketDistricts(state?: string) {
  const enabled = useMarketsEnabled();
  return useQuery({
    queryKey: ["markets", "meta", "districts", state ?? "national"],
    queryFn: () => getMarketDistricts({ state } satisfies MetaScope),
    staleTime: META_STALE,
    enabled,
  });
}

export function useMarketCommodities(scope: MetaScope) {
  const enabled = useMarketsEnabled();
  const { state, district, market } = scope;
  return useQuery({
    queryKey: ["markets", "meta", "commodities", state, district, market],
    queryFn: () => getMarketCommodities(scope),
    staleTime: META_STALE,
    enabled,
  });
}

export function useMarketMarkets(scope: MetaScope) {
  const enabled = useMarketsEnabled();
  const { state, district, commodity } = scope;
  return useQuery({
    queryKey: ["markets", "meta", "markets", state, district, commodity],
    queryFn: () => getMarketMarkets(scope),
    staleTime: META_STALE,
    enabled,
  });
}

export function useMarketVarieties(scope: MetaScope) {
  const baseEnabled = useMarketsEnabled();
  const { state, district, market, commodity } = scope;
  return useQuery({
    queryKey: ["markets", "meta", "varieties", state, district, market, commodity],
    queryFn: () => getMarketVarieties(scope),
    staleTime: META_STALE,
    enabled: baseEnabled && Boolean(commodity),
  });
}

export function useMarketGrades(scope: MetaScope) {
  const baseEnabled = useMarketsEnabled();
  const { state, district, market, commodity, variety } = scope;
  return useQuery({
    queryKey: [
      "markets",
      "meta",
      "grades",
      state,
      district,
      market,
      commodity,
      variety,
    ],
    queryFn: () => getMarketGrades(scope),
    staleTime: META_STALE,
    enabled: baseEnabled && Boolean(commodity),
  });
}
