"use client";

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  LayoutDashboard,
  Search,
  CloudSun,
  TrendingUp,
  Landmark as Government,
  Bot,
  BarChart3,
  Map,
  Settings,
  Bell,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useUiStore } from "@/stores/ui-store";

const pages = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard, keywords: "home main" },
  { label: "Disease Detection", href: "/disease", icon: Search, keywords: "disease detection scan" },
  { label: "Weather", href: "/weather", icon: CloudSun, keywords: "weather rain temperature forecast" },
  { label: "Markets", href: "/markets", icon: TrendingUp, keywords: "markets prices commodities" },
  { label: "Schemes", href: "/schemes", icon: Government, keywords: "schemes government subsidy" },
  { label: "AI Assistant", href: "/chat", icon: Bot, keywords: "chat ai assistant help" },
  { label: "Analytics", href: "/analytics", icon: BarChart3, keywords: "analytics reports charts" },
  { label: "Maps", href: "/map", icon: Map, keywords: "map satellite view" },
  { label: "Settings", href: "/settings", icon: Settings, keywords: "settings preferences" },
  { label: "Notifications", href: "/notifications", icon: Bell, keywords: "notifications alerts" },
];

const quickActions = [
  { label: "Go to Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "View Weather", href: "/weather", icon: CloudSun },
  { label: "Check Markets", href: "/markets", icon: TrendingUp },
  { label: "Find Schemes", href: "/schemes", icon: Government },
  { label: "Ask AI Assistant", href: "/chat", icon: Bot },
];

export function CommandPalette() {
  const router = useRouter();
  const { commandPaletteOpen, setCommandPaletteOpen } = useUiStore();

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }
      if (e.key === "Escape") {
        setCommandPaletteOpen(false);
      }
    },
    [commandPaletteOpen, setCommandPaletteOpen]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  const handleSelect = (href: string) => {
    setCommandPaletteOpen(false);
    router.push(href);
  };

  return (
    <AnimatePresence>
      {commandPaletteOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
          onClick={() => setCommandPaletteOpen(false)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: -20 }}
            transition={{ duration: 0.15 }}
            onClick={(e) => e.stopPropagation()}
            className="fixed left-1/2 top-[15%] w-full max-w-lg -translate-x-1/2"
          >
            <div className="overflow-hidden rounded-xl border border-border bg-card shadow-2xl">
              <Command className="w-full" label="Command palette">
                <div className="flex items-center border-b border-border px-4">
                  <Search className="mr-2 h-4 w-4 shrink-0 text-muted-foreground" />
                  <Command.Input
                    placeholder="Search pages or type a command..."
                    className="flex h-12 w-full bg-transparent text-sm text-foreground outline-none placeholder:text-muted-foreground"
                    autoFocus
                  />
                  <kbd className="hidden rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground sm:inline-flex items-center gap-0.5">
                    <span>ESC</span>
                  </kbd>
                </div>
                <Command.List className="max-h-72 overflow-y-auto p-2">
                  <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
                    No results found.
                  </Command.Empty>

                  <Command.Group heading="Quick Actions">
                    {quickActions.map(({ label, href, icon: Icon }) => (
                      <Command.Item
                        key={href}
                        value={label}
                        onSelect={() => handleSelect(href)}
                        className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-foreground aria-selected:bg-accent transition-colors"
                      >
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        <span className="flex-1">{label}</span>
                      </Command.Item>
                    ))}
                  </Command.Group>

                  <Command.Separator className="my-1 border-t border-border" />

                  <Command.Group heading="Pages">
                    {pages.map(({ label, href, icon: Icon, keywords }) => (
                      <Command.Item
                        key={href}
                        value={`${label} ${keywords}`}
                        onSelect={() => handleSelect(href)}
                        className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-foreground aria-selected:bg-accent transition-colors"
                      >
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        <span className="flex-1">{label}</span>
                        <kbd className="rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                          /{href.split("/").pop()}
                        </kbd>
                      </Command.Item>
                    ))}
                  </Command.Group>
                </Command.List>
              </Command>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
