import { useAuthStore } from "@/stores/auth-store";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

interface RequestConfig {
  method?: string;
  headers?: Record<string, string>;
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
  signal?: AbortSignal;
}

function buildUrl(path: string, params?: RequestConfig["params"]): string {
  const url = new URL(`${BASE_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

function getAuthHeaders(): Record<string, string> {
  const token = useAuthStore.getState().token;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export async function apiFetch<T = unknown>(
  path: string,
  config: RequestConfig = {}
): Promise<T> {
  const { method = "GET", headers = {}, body, params, signal } = config;

  const requestHeaders: Record<string, string> = {
    ...getAuthHeaders(),
    ...headers,
  };

  const requestInit: RequestInit = {
    method,
    headers: requestHeaders,
    signal,
  };

  if (body !== undefined) {
    if (body instanceof FormData) {
      requestInit.body = body;
    } else {
      requestInit.body = JSON.stringify(body);
      if (!requestHeaders["Content-Type"]) {
        requestHeaders["Content-Type"] = "application/json";
      }
    }
  }

  const url = buildUrl(path, params);

  try {
    const response = await fetch(url, requestInit);

    if (!response.ok) {
      let errorData: unknown;
      try {
        errorData = await response.json();
      } catch {
        try {
          errorData = await response.text();
        } catch {
          errorData = null;
        }
      }

      const message =
        typeof errorData === "object" &&
        errorData !== null &&
        "detail" in errorData
          ? String((errorData as { detail: unknown }).detail)
          : response.statusText || `Request failed with status ${response.status}`;

      throw new ApiError(message, response.status, errorData);
    }

    if (response.status === 204) {
      return undefined as T;
    }

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return (await response.json()) as T;
    }

    return (await response.text()) as unknown as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof TypeError && error.message === "Failed to fetch") {
      throw new ApiError("Network error. Please check your connection.", 0);
    }
    throw error;
  }
}

export function apiGet<T = unknown>(
  path: string,
  config?: RequestConfig
): Promise<T> {
  return apiFetch<T>(path, { ...config, method: "GET" });
}

export function apiPost<T = unknown>(
  path: string,
  body?: unknown,
  config?: RequestConfig
): Promise<T> {
  return apiFetch<T>(path, { ...config, method: "POST", body });
}

export function apiPut<T = unknown>(
  path: string,
  body?: unknown,
  config?: RequestConfig
): Promise<T> {
  return apiFetch<T>(path, { ...config, method: "PUT", body });
}

export function apiPatch<T = unknown>(
  path: string,
  body?: unknown,
  config?: RequestConfig
): Promise<T> {
  return apiFetch<T>(path, { ...config, method: "PATCH", body });
}

export function apiDelete<T = unknown>(
  path: string,
  config?: RequestConfig
): Promise<T> {
  return apiFetch<T>(path, { ...config, method: "DELETE" });
}
