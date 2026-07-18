import { apiGet, apiPost, apiPut, apiDelete } from "./api";
import type { Farm, Plot } from "@/types";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

// ---- Farms ----

export async function getFarms(params?: {
  page?: number;
  size?: number;
  search?: string;
  state?: string;
}): Promise<PaginatedResponse<Farm>> {
  return apiGet<PaginatedResponse<Farm>>("/api/v1/farms", {
    params: params as Record<string, string | number | boolean | undefined>,
  });
}

export async function getFarm(farmId: string): Promise<Farm> {
  return apiGet<Farm>(`/api/v1/farms/${farmId}`);
}

export async function createFarm(data: Omit<Farm, "id" | "farmer_id" | "created_at" | "plots">): Promise<Farm> {
  return apiPost<Farm>("/api/v1/farms", data);
}

export async function updateFarm(
  farmId: string,
  data: Partial<Omit<Farm, "id" | "farmer_id" | "created_at" | "plots">>
): Promise<Farm> {
  return apiPut<Farm>(`/api/v1/farms/${farmId}`, data);
}

export async function deleteFarm(farmId: string): Promise<void> {
  return apiDelete(`/api/v1/farms/${farmId}`);
}

// ---- Plots ----

export async function getPlots(params?: {
  farm_id?: string;
  page?: number;
  size?: number;
  crop_type?: string;
  status?: string;
}): Promise<PaginatedResponse<Plot>> {
  return apiGet<PaginatedResponse<Plot>>("/api/v1/plots", {
    params: params as Record<string, string | number | boolean | undefined>,
  });
}

export async function getPlot(plotId: string): Promise<Plot> {
  return apiGet<Plot>(`/api/v1/plots/${plotId}`);
}

export async function createPlot(
  data: Omit<Plot, "id" | "farmer_id" | "created_at">
): Promise<Plot> {
  return apiPost<Plot>("/api/v1/plots", data);
}

export async function updatePlot(
  plotId: string,
  data: Partial<Omit<Plot, "id" | "farmer_id" | "created_at">>
): Promise<Plot> {
  return apiPut<Plot>(`/api/v1/plots/${plotId}`, data);
}

export async function deletePlot(plotId: string): Promise<void> {
  return apiDelete(`/api/v1/plots/${plotId}`);
}

export async function getNearbyPlots(
  h3Index: string,
  params?: { radius_km?: number; resolution?: number }
): Promise<Plot[]> {
  return apiGet<Plot[]>(`/api/v1/plots/nearby/${h3Index}`, {
    params: params as Record<string, string | number | boolean | undefined>,
  });
}
