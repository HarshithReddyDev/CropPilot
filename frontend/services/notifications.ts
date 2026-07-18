import { apiGet, apiPost, apiPatch } from "./api";
import type { Notification } from "@/types";

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export async function listNotifications(params?: {
  page?: number;
  size?: number;
  is_read?: boolean;
  notification_type?: string;
}): Promise<PaginatedResponse<Notification>> {
  return apiGet<PaginatedResponse<Notification>>("/api/v1/notifications", {
    params: params as Record<string, string | number | boolean | undefined>,
  });
}

export async function markAsRead(
  notificationId: string
): Promise<Notification> {
  return apiPatch<Notification>(
    `/api/v1/notifications/${notificationId}/read`
  );
}

export async function markAllAsRead(): Promise<{ success: boolean }> {
  return apiPost<{ success: boolean }>("/api/v1/notifications/read-all");
}
