"use client";

import { useState, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Bell, Search, Menu, ChevronRight, Home, Mic } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import { LanguageSwitcher } from "@/components/shared/language-switcher";
import { useTranslation } from "@/lib/i18n";
import { useUiStore } from "@/stores/ui-store";

const pathKeys: Record<string, string> = {
  "/dashboard": "navigation.dashboard",
  "/disease": "navigation.disease",
  "/disease-detection": "navigation.disease",
  "/weather": "navigation.weather",
  "/markets": "navigation.markets",
  "/schemes": "navigation.schemes",
  "/chat": "navigation.assistant",
  "/ai-assistant": "navigation.assistant",
  "/analytics": "navigation.analytics",
  "/map": "navigation.maps",
  "/maps": "navigation.maps",
  "/farms": "navigation.dashboard",
  "/settings": "navigation.dashboard",
  "/notifications": "navigation.dashboard",
};

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { t } = useTranslation();
  const { setCommandPaletteOpen, setMobileMenuOpen, mobileMenuOpen } = useUiStore();
  const [unreadCount, setUnreadCount] = useState(3);

  const pathParts = pathname.split("/").filter(Boolean);
  const currentKey = pathKeys[pathname];
  const currentLabel = currentKey ? t(currentKey) : (pathParts[pathParts.length - 1] || "Dashboard");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setCommandPaletteOpen]);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/80 backdrop-blur-xl px-4 lg:px-6">
      <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-accent-foreground lg:hidden transition-colors"
        aria-label={t("common.menu")}
      >
        <Menu className="h-5 w-5" />
      </button>

      <nav className="hidden items-center gap-1.5 text-sm text-muted-foreground sm:flex">
        <Home className="h-4 w-4" />
        {pathParts.length > 0 ? (
          <>
            <ChevronRight className="h-3.5 w-3.5" />
            {pathParts.map((part, i) => {
              const href = "/" + pathParts.slice(0, i + 1).join("/");
              const key = pathKeys[href];
              const label = key ? t(key) : part.charAt(0).toUpperCase() + part.slice(1);
              const isLast = i === pathParts.length - 1;
              return (
                <span key={href} className="flex items-center gap-1.5">
                  {!isLast && <span className="hover:text-foreground cursor-pointer">{label}</span>}
                  {!isLast && <ChevronRight className="h-3.5 w-3.5" />}
                </span>
              );
            })}
            <span className="font-medium text-foreground">{currentLabel}</span>
          </>
        ) : (
          <span className="font-medium text-foreground">Dashboard</span>
        )}
      </nav>

      <div className="flex flex-1 items-center justify-end gap-3">
        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="hidden sm:flex items-center gap-2 rounded-lg border border-border bg-accent/50 px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent transition-colors w-full max-w-xs"
        >
          <Search className="h-4 w-4 shrink-0" />
          <span className="flex-1 text-start">{t("common.search")}…</span>
          <kbd className="hidden rounded border border-border bg-background px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground md:inline-flex items-center gap-0.5">
            <span className="text-xs">⌘</span>K
          </kbd>
        </button>

        <button
          onClick={() => setCommandPaletteOpen(true)}
          className="flex sm:hidden h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent transition-colors"
        >
          <Search className="h-5 w-5" />
        </button>

        <ThemeToggle />

        <LanguageSwitcher compact />

        {/* Global voice (§16): one assistant session from any page. */}
        <button
          onClick={() => {
            if (pathname === "/ai-assistant") {
              window.dispatchEvent(new CustomEvent("croppilot:start-voice"));
            } else {
              router.push("/ai-assistant?voice=1");
            }
          }}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label={t("voice.start")}
          title={t("voice.start")}
        >
          <Mic className="h-5 w-5" />
        </button>

        <button className="relative flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute -end-0.5 -top-0.5 flex h-4.5 min-w-[18px] items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground"
            >
              {unreadCount}
            </motion.span>
          )}
        </button>
      </div>
    </header>
  );
}
