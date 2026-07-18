import { apiPost, apiGet } from "./api";
import type { DiseaseLog } from "@/types";

export async function visionSync(
  plotId: string,
  formData: FormData
): Promise<DiseaseLog> {
  return apiPost<DiseaseLog>(`/api/v1/disease/vision-sync/${plotId}`, formData, {
    headers: {},
  });
}

export async function getDiseaseLog(
  logId: string
): Promise<DiseaseLog> {
  return apiGet<DiseaseLog>(`/api/v1/disease/logs/${logId}`);
}

export async function getPlotDiseaseLogs(
  plotId: string,
  params?: {
    page?: number;
    size?: number;
    severity?: string;
    is_resolved?: boolean;
    from_date?: string;
    to_date?: string;
  }
): Promise<{ items: DiseaseLog[]; total: number; page: number; size: number }> {
  return apiGet(`/api/v1/disease/logs`, {
    params: { plot_id: plotId, ...params } as Record<
      string,
      string | number | boolean | undefined
    >,
  });
}
