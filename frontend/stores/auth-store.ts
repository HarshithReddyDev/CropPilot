import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isDemoMode: boolean;
  setAuth: (token: string, refreshToken: string, user: User) => void;
  setUser: (user: User) => void;
  setTokens: (token: string, refreshToken: string) => void;
  logout: () => void;
  enableDemoMode: () => void;
  disableDemoMode: () => void;
}

const DEMO_USER: User = {
  id: "demo-user-1",
  email: "farmer@croppilot.in",
  full_name: "Ramesh Kumar",
  role: "farmer",
  state: "Telangana",
  is_active: true,
  is_verified: true,
  created_at: new Date().toISOString(),
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isDemoMode: false,

      setAuth: (token, refreshToken, user) =>
        set({
          token,
          refreshToken,
          user,
          isAuthenticated: true,
          isDemoMode: false,
        }),

      setUser: (user) => set({ user }),

      setTokens: (token, refreshToken) =>
        set({ token, refreshToken }),

      logout: () =>
        set({
          token: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
          isDemoMode: false,
        }),

      enableDemoMode: () =>
        set({
          token: null,
          refreshToken: null,
          user: DEMO_USER,
          isAuthenticated: true,
          isDemoMode: true,
        }),

      disableDemoMode: () =>
        set({
          token: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
          isDemoMode: false,
        }),
    }),
    {
      name: "croppilot-auth",
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        isDemoMode: state.isDemoMode,
      }),
    }
  )
);
