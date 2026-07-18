import { apiGet } from "./api";
import type { GovernmentScheme } from "@/types";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export async function getSchemes(params?: {
  state?: string;
  category?: string;
  page?: number;
  size?: number;
  search?: string;
}): Promise<PaginatedResponse<GovernmentScheme>> {
  return apiGet<PaginatedResponse<GovernmentScheme>>("/api/v1/schemes", {
    params: params as Record<string, string | number | boolean | undefined>,
  });
}
