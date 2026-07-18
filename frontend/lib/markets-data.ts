import type { MarketPrice } from "@/types";

export const MOCK_MARKET_PRICES: MarketPrice[] = [
  { id: "1", commodity: "Rice", variety: "Basmati", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 2200, max_price: 2800, modal_price: 2500, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "2", commodity: "Rice", variety: "IR-64", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 1800, max_price: 2400, modal_price: 2100, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "3", commodity: "Wheat", variety: "Sharbati", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 2100, max_price: 2600, modal_price: 2350, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "4", commodity: "Wheat", variety: "Lokwan", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 1950, max_price: 2450, modal_price: 2200, price_per_unit: "per quintal", arrival_date: "2026-07-17", source: "AGMARKNET" },
  { id: "5", commodity: "Maize", variety: "Hybrid", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 1600, max_price: 2000, modal_price: 1800, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "6", commodity: "Maize", variety: "Desi", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 1500, max_price: 1900, modal_price: 1700, price_per_unit: "per quintal", arrival_date: "2026-07-16", source: "AGMARKNET" },
  { id: "7", commodity: "Sugarcane", variety: "CO-86032", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 3200, max_price: 3800, modal_price: 3500, price_per_unit: "per tonne", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "8", commodity: "Sugarcane", variety: "CO-0238", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 3100, max_price: 3700, modal_price: 3400, price_per_unit: "per tonne", arrival_date: "2026-07-17", source: "AGMARKNET" },
  { id: "9", commodity: "Cotton", variety: "MCU-5", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 5800, max_price: 6500, modal_price: 6200, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "10", commodity: "Cotton", variety: "BT", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 5600, max_price: 6400, modal_price: 6000, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "11", commodity: "Groundnut", variety: "Java", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 4200, max_price: 4800, modal_price: 4500, price_per_unit: "per quintal", arrival_date: "2026-07-17", source: "AGMARKNET" },
  { id: "12", commodity: "Groundnut", variety: "Kadiri-6", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 4000, max_price: 4700, modal_price: 4350, price_per_unit: "per quintal", arrival_date: "2026-07-16", source: "AGMARKNET" },
  { id: "13", commodity: "Soybean", variety: "JS-335", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 3600, max_price: 4200, modal_price: 3900, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "14", commodity: "Soybean", variety: "Pusa-9712", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 3500, max_price: 4100, modal_price: 3800, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "15", commodity: "Mustard", variety: "Pusa Gold", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 4800, max_price: 5400, modal_price: 5100, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "16", commodity: "Mustard", variety: "Kranti", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 4600, max_price: 5200, modal_price: 4900, price_per_unit: "per quintal", arrival_date: "2026-07-17", source: "AGMARKNET" },
  { id: "17", commodity: "Potato", variety: "Kufri Jyoti", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 1200, max_price: 1600, modal_price: 1400, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "18", commodity: "Potato", variety: "Kufri Chandramukhi", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 1100, max_price: 1500, modal_price: 1300, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "19", commodity: "Onion", variety: "Red", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 1800, max_price: 2400, modal_price: 2100, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "20", commodity: "Onion", variety: "White", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 1700, max_price: 2300, modal_price: 2000, price_per_unit: "per quintal", arrival_date: "2026-07-17", source: "AGMARKNET" },
  { id: "21", commodity: "Tomato", variety: "Hybrid", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 800, max_price: 1400, modal_price: 1100, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "22", commodity: "Tomato", variety: "Desi", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 700, max_price: 1300, modal_price: 1000, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "23", commodity: "Tur (Arhar)", variety: "Pusa-992", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 5400, max_price: 6200, modal_price: 5800, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "24", commodity: "Tur (Arhar)", variety: "Local", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 5200, max_price: 6000, modal_price: 5600, price_per_unit: "per quintal", arrival_date: "2026-07-16", source: "AGMARKNET" },
  { id: "25", commodity: "Gram (Chana)", variety: "Desi", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 4800, max_price: 5600, modal_price: 5200, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "26", commodity: "Gram (Chana)", variety: "Kabuli", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 5000, max_price: 5800, modal_price: 5400, price_per_unit: "per quintal", arrival_date: "2026-07-17", source: "AGMARKNET" },
  { id: "27", commodity: "Moong", variety: "Pusa Vishal", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 5800, max_price: 6600, modal_price: 6200, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "28", commodity: "Moong", variety: "SML-668", market: "Koyambedu", district: "Chennai", state: "Tamil Nadu", min_price: 5600, max_price: 6400, modal_price: 6000, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "29", commodity: "Jowar", variety: "Maldandi", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 2200, max_price: 2800, modal_price: 2500, price_per_unit: "per quintal", arrival_date: "2026-07-17", source: "AGMARKNET" },
  { id: "30", commodity: "Bajra", variety: "Hybrid", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 1800, max_price: 2400, modal_price: 2100, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
  { id: "31", commodity: "Barley", variety: "PL-426", market: "Azadpur Mandi", district: "Central Delhi", state: "Delhi", min_price: 2000, max_price: 2600, modal_price: 2300, price_per_unit: "per quintal", arrival_date: "2026-07-16", source: "AGMARKNET" },
  { id: "32", commodity: "Potato", variety: "Kufri Sindhuri", market: "Gultekdi", district: "Pune", state: "Maharashtra", min_price: 1150, max_price: 1550, modal_price: 1350, price_per_unit: "per quintal", arrival_date: "2026-07-18", source: "AGMARKNET" },
];

export interface PriceHistoryPoint {
  date: string;
  price: number;
  commodity: string;
}

export const MOCK_PRICE_HISTORY: PriceHistoryPoint[] = [
  { date: "2026-01-01", price: 2200, commodity: "Rice" },
  { date: "2026-02-01", price: 2250, commodity: "Rice" },
  { date: "2026-03-01", price: 2350, commodity: "Rice" },
  { date: "2026-04-01", price: 2400, commodity: "Rice" },
  { date: "2026-05-01", price: 2450, commodity: "Rice" },
  { date: "2026-06-01", price: 2480, commodity: "Rice" },
  { date: "2026-07-01", price: 2500, commodity: "Rice" },
  { date: "2026-01-01", price: 2000, commodity: "Wheat" },
  { date: "2026-02-01", price: 2050, commodity: "Wheat" },
  { date: "2026-03-01", price: 2100, commodity: "Wheat" },
  { date: "2026-04-01", price: 2180, commodity: "Wheat" },
  { date: "2026-05-01", price: 2250, commodity: "Wheat" },
  { date: "2026-06-01", price: 2300, commodity: "Wheat" },
  { date: "2026-07-01", price: 2350, commodity: "Wheat" },
  { date: "2026-01-01", price: 1500, commodity: "Maize" },
  { date: "2026-02-01", price: 1550, commodity: "Maize" },
  { date: "2026-03-01", price: 1600, commodity: "Maize" },
  { date: "2026-04-01", price: 1650, commodity: "Maize" },
  { date: "2026-05-01", price: 1700, commodity: "Maize" },
  { date: "2026-06-01", price: 1750, commodity: "Maize" },
  { date: "2026-07-01", price: 1800, commodity: "Maize" },
  { date: "2026-01-01", price: 6000, commodity: "Cotton" },
  { date: "2026-02-01", price: 5900, commodity: "Cotton" },
  { date: "2026-03-01", price: 5850, commodity: "Cotton" },
  { date: "2026-04-01", price: 5950, commodity: "Cotton" },
  { date: "2026-05-01", price: 6050, commodity: "Cotton" },
  { date: "2026-06-01", price: 6150, commodity: "Cotton" },
  { date: "2026-07-01", price: 6200, commodity: "Cotton" },
  { date: "2026-01-01", price: 3400, commodity: "Sugarcane" },
  { date: "2026-02-01", price: 3450, commodity: "Sugarcane" },
  { date: "2026-03-01", price: 3480, commodity: "Sugarcane" },
  { date: "2026-04-01", price: 3500, commodity: "Sugarcane" },
  { date: "2026-05-01", price: 3480, commodity: "Sugarcane" },
  { date: "2026-06-01", price: 3520, commodity: "Sugarcane" },
  { date: "2026-07-01", price: 3500, commodity: "Sugarcane" },
];

export interface ForecastPoint {
  date: string;
  actual?: number;
  predicted: number;
  confidenceUpper: number;
  confidenceLower: number;
}

export const MOCK_PRICE_FORECAST: ForecastPoint[] = [
  { date: "Jul 11", actual: 2500, predicted: 2500, confidenceUpper: 2500, confidenceLower: 2500 },
  { date: "Jul 12", actual: 2520, predicted: 2520, confidenceUpper: 2520, confidenceLower: 2520 },
  { date: "Jul 13", actual: 2510, predicted: 2510, confidenceUpper: 2510, confidenceLower: 2510 },
  { date: "Jul 14", actual: 2530, predicted: 2530, confidenceUpper: 2530, confidenceLower: 2530 },
  { date: "Jul 15", actual: 2540, predicted: 2540, confidenceUpper: 2540, confidenceLower: 2540 },
  { date: "Jul 16", actual: 2535, predicted: 2535, confidenceUpper: 2535, confidenceLower: 2535 },
  { date: "Jul 17", actual: 2550, predicted: 2550, confidenceUpper: 2550, confidenceLower: 2550 },
  { date: "Jul 18", predicted: 2570, confidenceUpper: 2620, confidenceLower: 2520 },
  { date: "Jul 19", predicted: 2590, confidenceUpper: 2660, confidenceLower: 2520 },
  { date: "Jul 20", predicted: 2580, confidenceUpper: 2670, confidenceLower: 2490 },
  { date: "Jul 21", predicted: 2610, confidenceUpper: 2710, confidenceLower: 2510 },
  { date: "Jul 22", predicted: 2630, confidenceUpper: 2740, confidenceLower: 2520 },
  { date: "Jul 23", predicted: 2620, confidenceUpper: 2750, confidenceLower: 2490 },
  { date: "Jul 24", predicted: 2650, confidenceUpper: 2800, confidenceLower: 2500 },
];

export interface SellingWindow {
  date: string;
  day: string;
  score: "best" | "good" | "avoid";
}

export const MOCK_SELLING_WINDOWS: SellingWindow[] = (() => {
  const windows: SellingWindow[] = [];
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const start = new Date(2026, 6, 1);
  for (let i = 0; i < 31; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    const dayScore: SellingWindow["score"] =
      i >= 10 && i <= 15 ? "best" :
      i >= 5 && i <= 8 ? "avoid" :
      i >= 22 && i <= 25 ? "best" :
      i >= 28 ? "good" :
      "good";
    windows.push({
      date: d.toISOString().slice(0, 10),
      day: days[d.getDay()],
      score: dayScore,
    });
  }
  return windows;
})();

export interface AIRecommendation {
  action: "sell" | "wait";
  currentPrice: number;
  predictedPrice: number;
  confidence: number;
  reasoning: string[];
  factors: { name: string; impact: "positive" | "negative" | "neutral" }[];
}

export const MOCK_AI_RECOMMENDATION: AIRecommendation = {
  action: "sell",
  currentPrice: 2550,
  predictedPrice: 2650,
  confidence: 87,
  reasoning: [
    "Price expected to peak in the next 3-4 days",
    "Market arrival is decreasing, reducing supply",
    "Festival season approaching, demand expected to rise",
  ],
  factors: [
    { name: "Weather conditions", impact: "positive" },
    { name: "Market demand", impact: "positive" },
    { name: "Seasonal trend", impact: "positive" },
    { name: "Transportation costs", impact: "negative" },
    { name: "Storage availability", impact: "neutral" },
  ],
};
