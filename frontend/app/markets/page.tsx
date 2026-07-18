"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Filter } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { PriceTable } from "@/components/markets/price-table";
import { PriceChart } from "@/components/markets/price-chart";
import { PriceForecast } from "@/components/markets/price-forecast";
import { AIRecommendationCard } from "@/components/markets/ai-recommendation";
import { BestSellingTime } from "@/components/markets/best-selling-time";
import { TopCommodities } from "@/components/markets/top-commodities";
import { INDIAN_STATES, COMMODITIES } from "@/lib/constants";
import {
  MOCK_MARKET_PRICES,
  MOCK_PRICE_HISTORY,
  MOCK_PRICE_FORECAST,
  MOCK_AI_RECOMMENDATION,
  MOCK_SELLING_WINDOWS,
} from "@/lib/markets-data";
import { cn } from "@/lib/utils";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function MarketsPage() {
  const [commoditySearch, setCommoditySearch] = useState("");
  const [selectedState, setSelectedState] = useState<string>("all");
  const [selectedMarket, setSelectedMarket] = useState<string>("all");

  const markets = [...new Set(MOCK_MARKET_PRICES.map((p) => p.market))];

  const filteredPrices = MOCK_MARKET_PRICES.filter((p) => {
    if (commoditySearch && !p.commodity.toLowerCase().includes(commoditySearch.toLowerCase())) return false;
    if (selectedState !== "all" && p.state !== selectedState) return false;
    if (selectedMarket !== "all" && p.market !== selectedMarket) return false;
    return true;
  });

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div>
          <h1 className="text-2xl font-bold text-foreground">Market Intelligence</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Live mandi prices, historical trends, and AI-powered selling recommendations
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px] max-w-xs">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search commodity..."
              value={commoditySearch}
              onChange={(e) => setCommoditySearch(e.target.value)}
              className="h-9 w-full rounded-lg border border-input bg-background pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>

          <Select value={selectedState} onValueChange={setSelectedState}>
            <SelectTrigger className="h-9 w-44">
              <SelectValue placeholder="All States" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All States</SelectItem>
              {INDIAN_STATES.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={selectedMarket} onValueChange={setSelectedMarket}>
            <SelectTrigger className="h-9 w-44">
              <SelectValue placeholder="All Markets" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Markets</SelectItem>
              {markets.map((m) => (
                <SelectItem key={m} value={m}>{m}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <PriceTable data={filteredPrices} />
            <PriceChart data={MOCK_PRICE_HISTORY} />
            <PriceForecast data={MOCK_PRICE_FORECAST} />
            <div className="grid gap-6 sm:grid-cols-2">
              <AIRecommendationCard data={MOCK_AI_RECOMMENDATION} />
              <BestSellingTime data={MOCK_SELLING_WINDOWS} />
            </div>
          </div>
          <div className="space-y-6">
            <TopCommodities data={MOCK_MARKET_PRICES} />
            <div className="rounded-xl border border-border bg-card p-4">
              <h3 className="text-sm font-semibold text-foreground">Market Summary</h3>
              <div className="mt-3 space-y-3">
                {[
                  { label: "Total Markets", value: markets.length },
                  { label: "Commodities Tracked", value: COMMODITIES.length },
                  { label: "States Covered", value: new Set(MOCK_MARKET_PRICES.map((p) => p.state)).size },
                  { label: "Records Updated", value: new Date().toLocaleDateString("en-IN") },
                ].map(({ label, value }) => (
                  <div key={label} className="flex items-center justify-between border-b border-border/50 pb-2 last:border-0">
                    <span className="text-xs text-muted-foreground">{label}</span>
                    <span className="text-sm font-semibold text-foreground">{value}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-card p-4">
              <h3 className="text-sm font-semibold text-foreground">Quick Tips</h3>
              <ul className="mt-3 space-y-2">
                {[
                  "Compare prices across multiple mandis for best rates",
                  "Use AI forecast to time your crop selling",
                  "Green marked days are optimal selling windows",
                  "Price trends help identify seasonal patterns",
                ].map((tip, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] text-primary font-medium">{i + 1}</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </motion.div>
    </DashboardLayout>
  );
}
