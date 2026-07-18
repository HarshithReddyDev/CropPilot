import { apiGet } from "./api";
import type { MarketPrice } from "@/types";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

interface PriceQueryParams {
  commodity?: string;
  state?: string;
  district?: string;
  market?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export async function queryPrices(
  params: PriceQueryParams
): Promise<PaginatedResponse<MarketPrice>> {
  return apiGet<PaginatedResponse<MarketPrice>>("/api/v1/market/prices", {
    params: params as Record<string, string | number | boolean | undefined>,
  });
}

export async function getLatestPrices(
  commodity: string,
  state?: string
): Promise<MarketPrice[]> {
  return apiGet<MarketPrice[]>("/api/v1/market/prices/latest", {
    params: {
      commodity,
      state: state || undefined,
    },
  });
}
