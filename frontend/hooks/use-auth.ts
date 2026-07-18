"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth-store";
import * as authApi from "@/services/auth";
import { ApiError } from "@/services/api";

export function useAuth() {
  const queryClient = useQueryClient();
  const store = useAuthStore();

  const profileQuery = useQuery({
    queryKey: ["auth", "profile"],
    queryFn: () => authApi.getProfile(),
    enabled: store.isAuthenticated && !store.isDemoMode,
    retry: false,
    staleTime: 5 * 60 * 1000,
    refetchOnMount: true,
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      store.setAuth(data.access_token, data.refresh_token, data.user);
      queryClient.setQueryData(["auth", "profile"], data.user);
    },
  });

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      store.setAuth(data.access_token, data.refresh_token, data.user);
      queryClient.setQueryData(["auth", "profile"], data.user);
    },
  });

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      store.logout();
      queryClient.clear();
    },
  });

  return {
    user: store.user,
    token: store.token,
    isAuthenticated: store.isAuthenticated,
    isDemoMode: store.isDemoMode,
    isLoading: profileQuery.isLoading || loginMutation.isPending || registerMutation.isPending,
    login: loginMutation,
    register: registerMutation,
    logout: logoutMutation,
    enableDemoMode: store.enableDemoMode,
    disableDemoMode: store.disableDemoMode,
    loginError: loginMutation.error ? (loginMutation.error as ApiError).message || "Login failed" : null,
    registerError: registerMutation.error ? (registerMutation.error as ApiError).message || "Registration failed" : null,
  };
}
