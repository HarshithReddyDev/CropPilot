"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Search,
  CloudSun,
  TrendingUp,
  Landmark as Government,
  Bot,
  BarChart3,
  Map,
  Sprout,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useUiStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/shared/theme-toggle";

const navItems = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Disease Detection", href: "/disease-detection", icon: Search },
  { label: "Weather", href: "/weather", icon: CloudSun },
  { label: "Markets", href: "/markets", icon: TrendingUp },
  { label: "Schemes", href: "/schemes", icon: Government },
  { label: "AI Assistant", href: "/ai-assistant", icon: Bot },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Maps", href: "/maps", icon: Map },
];

const sidebarWidth = 256;
const sidebarCollapsed = 68;

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUiStore();

  return (
    <motion.aside
      animate={{ width: sidebarOpen ? sidebarWidth : sidebarCollapsed }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="flex h-screen flex-col border-r border-sidebar-border bg-sidebar overflow-hidden shrink-0"
    >
      <div className="flex h-16 items-center gap-3 border-b border-sidebar-border px-4">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground shrink-0">
          <Sprout className="h-4 w-4" />
        </div>
        <AnimatePresence mode="wait">
          {sidebarOpen && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              className="text-lg font-bold text-sidebar-foreground whitespace-nowrap overflow-hidden"
            >
              CropPilot
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3 scrollbar-hide">
        {navItems.map(({ label, href, icon: Icon }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors relative",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-muted hover:text-sidebar-foreground"
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              <AnimatePresence mode="wait">
                {sidebarOpen && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="truncate"
                  >
                    {label}
                  </motion.span>
                )}
              </AnimatePresence>
              {isActive && (
                <motion.div
                  layoutId="activeNav"
                  className="absolute inset-0 rounded-lg bg-primary/10 -z-10"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-sidebar-border p-3">
        <div className="flex items-center gap-3 rounded-lg px-3 py-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-primary text-sm font-semibold">
            HR
          </div>
          <AnimatePresence mode="wait">
            {sidebarOpen && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex-1 truncate"
              >
                <p className="text-sm font-medium text-sidebar-foreground truncate">
                  Harsh Raj
                </p>
                <p className="text-xs text-sidebar-foreground/60 truncate">
                  Farmer
                </p>
              </motion.div>
            )}
          </AnimatePresence>
          {sidebarOpen && (
            <div className="flex items-center gap-1">
              <ThemeToggle />
              <button className="flex h-8 w-8 items-center justify-center rounded-lg text-sidebar-foreground/60 hover:bg-sidebar-muted hover:text-sidebar-foreground transition-colors">
                <Settings className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        <button
          onClick={toggleSidebar}
          className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm text-sidebar-foreground/60 hover:bg-sidebar-muted hover:text-sidebar-foreground transition-colors"
        >
          {sidebarOpen ? (
            <>
              <ChevronLeft className="h-4 w-4" />
              <AnimatePresence mode="wait">
                {sidebarOpen && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    Collapse
                  </motion.span>
                )}
              </AnimatePresence>
            </>
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>
      </div>
    </motion.aside>
  );
}
