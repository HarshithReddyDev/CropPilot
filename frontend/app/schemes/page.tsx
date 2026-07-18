"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { SchemeCard } from "@/components/schemes/scheme-card";
import { SchemeDetail } from "@/components/schemes/scheme-detail";
import { MOCK_SCHEMES, SCHEME_CATEGORIES } from "@/lib/schemes-data";
import { cn } from "@/lib/utils";
import type { GovernmentScheme } from "@/types";

export default function SchemesPage() {
  const [activeCategory, setActiveCategory] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedScheme, setSelectedScheme] = useState<GovernmentScheme | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const filtered = useMemo(() => {
    return MOCK_SCHEMES.filter((s) => {
      if (activeCategory !== "All" && s.category !== activeCategory) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        return (
          s.scheme_name.toLowerCase().includes(q) ||
          s.description.toLowerCase().includes(q) ||
          s.tags.some((t) => t.toLowerCase().includes(q)) ||
          s.ministry?.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [activeCategory, searchQuery]);

  const handleViewDetail = (scheme: GovernmentScheme) => {
    setSelectedScheme(scheme);
    setDetailOpen(true);
  };

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div>
          <h1 className="text-2xl font-bold text-foreground">Government Schemes</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Discover and apply for agricultural schemes, subsidies, and welfare programs
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search schemes by name, description, tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-9 w-full rounded-lg border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {SCHEME_CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={cn(
                "rounded-full px-4 py-1.5 text-xs font-medium transition-colors",
                activeCategory === cat
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80"
              )}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((scheme) => (
            <SchemeCard
              key={scheme.id}
              scheme={scheme}
              onViewDetail={handleViewDetail}
            />
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
              <Search className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="mt-4 text-lg font-semibold text-foreground">No schemes found</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Try adjusting your search or filter criteria
            </p>
          </div>
        )}
      </motion.div>

      <SchemeDetail
        scheme={selectedScheme}
        open={detailOpen}
        onOpenChange={setDetailOpen}
      />
    </DashboardLayout>
  );
}
