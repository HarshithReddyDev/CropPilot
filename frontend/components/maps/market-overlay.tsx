"use client";

import { useMemo } from "react";
import { ScatterplotLayer } from "@deck.gl/layers";

interface MarketLocation {
  name: string;
  position: [number, number];
  volume: number;
  price: number;
  commodities?: string[];
  priceRange?: { min: number; max: number };
}

const markets: MarketLocation[] = [
  { name: "Hyderabad Mandi", position: [78.48, 17.38], volume: 35000, price: 3100, commodities: ["Rice", "Wheat", "Maize"], priceRange: { min: 2800, max: 3500 } },
  { name: "Warangal Market", position: [79.58, 17.97], volume: 22000, price: 2950, commodities: ["Cotton", "Maize"], priceRange: { min: 2650, max: 3200 } },
  { name: "Nizamabad Mandi", position: [78.10, 18.67], volume: 18000, price: 3050, commodities: ["Rice", "Sugarcane"], priceRange: { min: 2800, max: 3400 } },
  { name: "Khammam Market", position: [80.15, 17.25], volume: 15000, price: 2880, commodities: ["Cotton", "Maize"], priceRange: { min: 2550, max: 3100 } },
  { name: "Karimnagar Mandi", position: [79.13, 18.44], volume: 12000, price: 2980, commodities: ["Wheat", "Cotton"], priceRange: { min: 2700, max: 3300 } },
  { name: "Mahbubnagar Market", position: [77.99, 16.74], volume: 9000, price: 2800, commodities: ["Maize", "Groundnut"], priceRange: { min: 2500, max: 3000 } },
  { name: "Nalgonda Market", position: [79.27, 17.06], volume: 8000, price: 2750, commodities: ["Rice", "Cotton"], priceRange: { min: 2450, max: 2950 } },
  { name: "Adilabad Market", position: [78.53, 19.67], volume: 6000, price: 2700, commodities: ["Maize", "Cotton"], priceRange: { min: 2400, max: 2900 } },
  { name: "Siddipet Market", position: [78.85, 18.10], volume: 11000, price: 2920, commodities: ["Rice", "Wheat"], priceRange: { min: 2600, max: 3150 } },
  { name: "Medak Market", position: [78.25, 18.02], volume: 7500, price: 2850, commodities: ["Sugarcane", "Maize"], priceRange: { min: 2500, max: 3100 } },
];

function getPriceColor(price: number): [number, number, number, number] {
  if (price >= 3000) return [239, 68, 68, 200];
  if (price >= 2900) return [251, 191, 36, 200];
  return [34, 197, 94, 200];
}

interface MarketOverlayProps {
  onMarketClick?: (market: MarketLocation) => void;
}

export function MarketOverlay({ onMarketClick }: MarketOverlayProps) {
  return useMemo(
    () =>
      new ScatterplotLayer({
        id: "market-overlay",
        data: markets,
        getPosition: (d: MarketLocation) => d.position,
        getFillColor: (d: MarketLocation) => getPriceColor(d.price),
        getRadius: (d: MarketLocation) => Math.sqrt(d.volume) * 2,
        radiusMinPixels: 6,
        radiusMaxPixels: 50,
        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 255, 150],
        stroked: true,
        getLineColor: [255, 255, 255, 100],
        getLineWidth: 1,
        lineWidthMinPixels: 1,
        onClick: (info: any) => {
          if (info.object && onMarketClick) {
            onMarketClick(info.object);
          }
        },
        updateTriggers: {
          getFillColor: [markets],
          getRadius: [markets],
        },
      }),
    [onMarketClick]
  );
}

export type { MarketLocation };
