import { apiGet } from "./api";
import type {
  LatestPricesResponse,
  MarketComparisonResponse,
  MarketHistoryResponse,
  MarketMetaResponse,
  MarketOverview,
} from "@/types";

const BASE = "/api/v1/markets";

export interface LatestQuery {
  state?: string;
  district?: string;
  commodity?: string;
  market?: string;
  variety?: string;
  grade?: string;
  limit?: number;
  offset?: number;
}

export interface HistoryQuery {
  commodity: string;
  state?: string;
  district?: string;
  market?: string;
  variety?: string;
  grade?: string;
  days?: 7 | 30 | 90;
  from_date?: string;
  to_date?: string;
}

export interface ComparisonQuery {
  commodity: string;
  state?: string;
  district?: string;
  variety?: string;
  grade?: string;
}

export interface MetaScope {
  state?: string;
  district?: string;
  market?: string;
  commodity?: string;
  variety?: string;
}

type Params = Record<string, string | number | boolean | undefined>;

function clean<T extends object>(params: T): Params {
  return { ...(params as object) } as unknown as Params;
}

export async function getMarketsLatest(
  params: LatestQuery = {}
): Promise<LatestPricesResponse> {
  return apiGet<LatestPricesResponse>(`${BASE}/latest`, {
    params: params as Params,
  });
}

export async function getMarketsHistory(
  params: HistoryQuery
): Promise<MarketHistoryResponse> {
  return apiGet<MarketHistoryResponse>(`${BASE}/history`, {
    params: clean(params),
  });
}

export async function getMarketsComparison(
  params: ComparisonQuery
): Promise<MarketComparisonResponse> {
  return apiGet<MarketComparisonResponse>(`${BASE}/comparison`, {
    params: clean(params),
  });
}

export async function getMarketsOverview(
  state?: string
): Promise<MarketOverview> {
  return apiGet<MarketOverview>(`${BASE}/overview`, {
    params: { state } as Params,
  });
}

export async function getMarketStates(): Promise<MarketMetaResponse> {
  return apiGet<MarketMetaResponse>(`${BASE}/meta/states`);
}

export async function getMarketDistricts(
  scope: MetaScope = {}
): Promise<MarketMetaResponse> {
  return apiGet<MarketMetaResponse>(`${BASE}/meta/districts`, {
    params: clean(scope),
  });
}

export async function getMarketCommodities(
  scope: MetaScope = {}
): Promise<MarketMetaResponse> {
  return apiGet<MarketMetaResponse>(`${BASE}/meta/commodities`, {
    params: clean(scope),
  });
}

export async function getMarketMarkets(
  scope: MetaScope = {}
): Promise<MarketMetaResponse> {
  return apiGet<MarketMetaResponse>(`${BASE}/meta/markets`, {
    params: clean(scope),
  });
}

export async function getMarketVarieties(
  scope: MetaScope = {}
): Promise<MarketMetaResponse> {
  return apiGet<MarketMetaResponse>(`${BASE}/meta/varieties`, {
    params: clean(scope),
  });
}

export async function getMarketGrades(
  scope: MetaScope = {}
): Promise<MarketMetaResponse> {
  return apiGet<MarketMetaResponse>(`${BASE}/meta/grades`, {
    params: clean(scope),
  });
}
