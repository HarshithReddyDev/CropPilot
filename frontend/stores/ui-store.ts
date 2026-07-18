import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "light" | "dark" | "system";
type ActivePage =
  | "dashboard"
  | "farms"
  | "map"
  | "disease"
  | "weather"
  | "markets"
  | "schemes"
  | "analytics"
  | "chat"
  | "notifications"
  | "settings";

interface UiState {
  sidebarOpen: boolean;
  theme: Theme;
  commandPaletteOpen: boolean;
  activePage: ActivePage;
  mobileMenuOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: Theme) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setActivePage: (page: ActivePage) => void;
  setMobileMenuOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: "system",
      commandPaletteOpen: false,
      activePage: "dashboard",
      mobileMenuOpen: false,

      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
      setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
      setActivePage: (page) => set({ activePage: page }),
      setMobileMenuOpen: (open) => set({ mobileMenuOpen: open }),
    }),
    {
      name: "croppilot-ui",
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        theme: state.theme,
        activePage: state.activePage,
      }),
    }
  )
);
