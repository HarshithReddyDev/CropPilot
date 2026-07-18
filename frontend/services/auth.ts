import { apiPost, apiGet, apiFetch } from "./api";
import type { User } from "@/types";

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  role?: "farmer" | "analyst" | "admin";
  state?: string;
  district?: string;
}

interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

interface RefreshResponse {
  access_token: string;
  refresh_token: string;
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append("username", data.email);
  formData.append("password", data.password);

  const tokenData = await apiFetch<{
    access_token: string;
    refresh_token: string;
    token_type: string;
  }>("/api/v1/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });

  const user = await getProfile(tokenData.access_token);

  return {
    access_token: tokenData.access_token,
    refresh_token: tokenData.refresh_token,
    user,
  };
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  return apiPost<AuthResponse>("/api/v1/auth/register", data);
}

export async function refresh(
  refreshToken: string
): Promise<RefreshResponse> {
  return apiPost<RefreshResponse>("/api/v1/auth/refresh", {
    refresh_token: refreshToken,
  });
}

export async function logout(): Promise<void> {
  try {
    await apiPost("/api/v1/auth/logout");
  } catch {
    // Ignore server errors during logout — clear local state regardless
  }
}

export async function getProfile(
  tokenOverride?: string
): Promise<User> {
  if (tokenOverride) {
    return apiGet<User>("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${tokenOverride}` },
    });
  }
  return apiGet<User>("/api/v1/auth/me");
}
