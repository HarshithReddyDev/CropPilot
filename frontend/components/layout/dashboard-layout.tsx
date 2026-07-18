"use client";

import { type ReactNode, useEffect } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { CommandPalette } from "./command-palette";
import { useUiStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const { mobileMenuOpen, setMobileMenuOpen } = useUiStore();

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname, setMobileMenuOpen]);

  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <div className="hidden lg:flex">
        <Sidebar />
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileMenuOpen(false)}
              className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="fixed inset-y-0 left-0 z-50 w-72 lg:hidden"
            >
              <div className="relative h-full">
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="absolute -right-10 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-card shadow-lg border border-border"
                >
                  <X className="h-4 w-4" />
                </button>
                <Sidebar />
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="flex flex-1 flex-col min-w-0">
        <Header />
        <main
          className={cn(
            "flex-1 overflow-y-auto p-4 lg:p-6 bg-background"
          )}
        >
          {children}
        </main>
      </div>

      <CommandPalette />
    </div>
  );
}
