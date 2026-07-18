import type { ChatMessage, AnalyticsData, H3HexFeature } from "@/types";

// ---- Navigation ----

export interface NavItem {
  label: string;
  href: string;
  icon: string;
  badge?: number;
}

export const SIDEBAR_NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard" },
  { label: "Disease Detection", href: "/disease-detection", icon: "Bug" },
  { label: "Weather", href: "/weather", icon: "CloudSun" },
  { label: "Markets", href: "/markets", icon: "TrendingUp" },
  { label: "Schemes", href: "/schemes", icon: "Government" },
  { label: "AI Assistant", href: "/ai-assistant", icon: "MessageSquare" },
  { label: "Analytics", href: "/analytics", icon: "BarChart3" },
  { label: "Maps", href: "/maps", icon: "Map" },
];

// ---- Feature Flags ----

export const FEATURE_FLAGS = {
  MAPBOX: true,
  DECK_GL: true,
  DISEASE_DETECTION: true,
  AI_CHAT: true,
  MARKET_DATA: true,
  GOVERNMENT_SCHEMES: true,
  WEATHER_FORECAST: true,
  ANALYTICS: true,
  NOTIFICATIONS: true,
  OFFLINE_MODE: false,
  DARK_MODE: true,
  BATCH_UPLOAD: false,
} as const;

// ---- Commodities ----

export const COMMODITIES = [
  "Rice",
  "Wheat",
  "Maize",
  "Sugarcane",
  "Cotton",
  "Groundnut",
  "Soybean",
  "Mustard",
  "Potato",
  "Onion",
  "Tomato",
  "Tur (Arhar)",
  "Gram (Chana)",
  "Moong",
  "Urad",
  "Masoor",
  "Jowar",
  "Bajra",
  "Ragi",
  "Barley",
] as const;

// ---- Indian States ----

export const INDIAN_STATES = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
] as const;

// ---- Chart Configurations ----

export const CHART_COLORS = {
  primary: "#22c55e",
  secondary: "#3b82f6",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#06b6d4",
  purple: "#8b5cf6",
  pink: "#ec4899",
} as const;

export const CHART_DEFAULTS = {
  yield: {
    colors: [CHART_COLORS.primary, CHART_COLORS.secondary],
    fillOpacity: 0.15,
  },
  revenue: {
    colors: [CHART_COLORS.secondary, CHART_COLORS.info],
    fillOpacity: 0.1,
  },
  weather: {
    tempColor: CHART_COLORS.warning,
    humidityColor: CHART_COLORS.info,
    rainColor: CHART_COLORS.primary,
  },
  disease: {
    healthyColor: CHART_COLORS.primary,
    infectedColor: CHART_COLORS.danger,
    atRiskColor: CHART_COLORS.warning,
  },
} as const;

// ---- Mock Data ----

export const MOCK_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: "1",
    role: "assistant",
    content:
      "Hello! I'm your AI agricultural assistant. How can I help you today? I can answer questions about crop diseases, weather patterns, market prices, and government schemes.",
    timestamp: new Date().toISOString(),
  },
];

export const MOCK_ANALYTICS_DATA: AnalyticsData = {
  revenue: [45000, 52000, 48000, 61000, 58000, 72000, 68000, 75000, 82000, 79000, 88000, 95000],
  yield: [2.8, 3.1, 2.9, 3.4, 3.2, 3.8, 3.6, 4.0, 4.2, 3.9, 4.5, 4.8],
  crop_health: 78,
  water_usage: [120, 115, 130, 125, 140, 135, 110, 105, 100, 95, 90, 85],
  fertilizer_usage: [40, 42, 38, 45, 43, 50, 48, 52, 55, 51, 58, 60],
  dates: [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ],
};

export const MOCK_H3_FEATURES: H3HexFeature[] = [
  { h3_index: "8928308280fffff", confidence: 0.85, crop_type: "Rice", color: [34, 197, 94, 180] },
  { h3_index: "8928308281fffff", confidence: 0.32, crop_type: "Wheat", color: [239, 68, 68, 180] },
  { h3_index: "8928308282fffff", confidence: 0.67, crop_type: "Cotton", color: [251, 191, 36, 180] },
  { h3_index: "8928308283fffff", confidence: 0.91, crop_type: "Sugarcane", color: [34, 197, 94, 180] },
  { h3_index: "8928308284fffff", confidence: 0.45, crop_type: "Maize", color: [251, 191, 36, 180] },
  { h3_index: "8928308285fffff", confidence: 0.73, crop_type: "Rice", color: [34, 197, 94, 180] },
];

// ---- Theme ----

export const THEME_STORAGE_KEY = "croppilot-theme";

export interface CropHealthData {
  crop: string;
  health: number;
  color: string;
}

export interface HourlyForecast {
  time: string;
  temp: number;
  icon: string;
}

export interface ExpenseBreakdown {
  category: string;
  amount: number;
  color: string;
}

export interface CropYieldData {
  crop: string;
  yield: number;
  target: number;
}

export interface CommodityPrice {
  commodity: string;
  price: number;
  change: number;
}

export interface DiseaseAlert {
  id: string;
  disease: string;
  crop: string;
  severity: "high" | "medium" | "low";
  time: string;
  plot: string;
}

export interface DashboardNotification {
  id: string;
  type: "info" | "alert" | "warning" | "success";
  title: string;
  body: string;
  time: string;
  isRead: boolean;
}

export interface DashboardData {
  farmOverview: {
    totalFarms: number;
    totalAreaHectares: number;
    activePlots: number;
    currentSeason: string;
  };
  weather: {
    temperature: number;
    feelsLike: number;
    humidity: number;
    windSpeed: number;
    weatherMain: string;
    weatherDescription: string;
    location: string;
    hourlyForecast: HourlyForecast[];
  };
  cropHealth: {
    overallScore: number;
    crops: CropHealthData[];
    trend: number;
  };
  diseaseAlerts: {
    total: number;
    alerts: DiseaseAlert[];
  };
  notifications: DashboardNotification[];
  revenue: {
    total: number;
    monthly: { month: string; revenue: number }[];
    comparison: number;
  };
  expenses: {
    total: number;
    breakdown: ExpenseBreakdown[];
    comparison: number;
  };
  profit: {
    netProfit: number;
    margin: number;
    trend: number[];
    trendDirection: "up" | "down";
  };
  yield: {
    total: number;
    perHectare: number;
    cropWise: CropYieldData[];
    target: number;
  };
  marketTrends: {
    marketName: string;
    commodities: CommodityPrice[];
    priceHistory: { day: string; prices: { commodity: string; price: number }[] }[];
    gainers: CommodityPrice[];
    losers: CommodityPrice[];
  };
  schemeRecommendations: {
    id: string;
    name: string;
    description: string;
    eligibility: string;
    benefits: string;
  }[];
}

export const MOCK_DASHBOARD_DATA: DashboardData = {
  farmOverview: {
    totalFarms: 3,
    totalAreaHectares: 45.2,
    activePlots: 12,
    currentSeason: "Kharif 2025",
  },
  weather: {
    temperature: 32,
    feelsLike: 36,
    humidity: 68,
    windSpeed: 12,
    weatherMain: "Sunny",
    weatherDescription: "Partly cloudy with sunny spells",
    location: "Punjab, IN",
    hourlyForecast: [
      { time: "12:00", temp: 32, icon: "sun" },
      { time: "13:00", temp: 33, icon: "sun" },
      { time: "14:00", temp: 34, icon: "cloud-sun" },
      { time: "15:00", temp: 33, icon: "cloud-sun" },
      { time: "16:00", temp: 31, icon: "cloud" },
      { time: "17:00", temp: 29, icon: "cloud" },
    ],
  },
  cropHealth: {
    overallScore: 82,
    crops: [
      { crop: "Rice", health: 85, color: "#22c55e" },
      { crop: "Cotton", health: 72, color: "#f59e0b" },
      { crop: "Vegetables", health: 90, color: "#3b82f6" },
    ],
    trend: 3.2,
  },
  diseaseAlerts: {
    total: 4,
    alerts: [
      { id: "1", disease: "Leaf Blight", crop: "Rice", severity: "high", time: "2h ago", plot: "Plot A-3" },
      { id: "2", disease: "Powdery Mildew", crop: "Cotton", severity: "medium", time: "5h ago", plot: "Plot B-1" },
      { id: "3", disease: "Aphid Infestation", crop: "Vegetables", severity: "low", time: "1d ago", plot: "Plot C-2" },
      { id: "4", disease: "Root Rot", crop: "Rice", severity: "medium", time: "2d ago", plot: "Plot A-1" },
    ],
  },
  notifications: [
    { id: "1", type: "alert", title: "Disease Detected", body: "Leaf Blight detected in Plot A-3. Take immediate action.", time: "2h ago", isRead: false },
    { id: "2", type: "info", title: "Weather Alert", body: "Heavy rainfall expected in your region tomorrow.", time: "5h ago", isRead: false },
    { id: "3", type: "warning", title: "Irrigation Reminder", body: "Plot B-1 due for irrigation in 2 days.", time: "1d ago", isRead: false },
    { id: "4", type: "success", title: "Scheme Approved", body: "Your PM-KISAN application has been approved.", time: "2d ago", isRead: true },
    { id: "5", type: "info", title: "Market Update", body: "Wheat prices increased by 5% in local mandi.", time: "3d ago", isRead: true },
  ],
  revenue: {
    total: 892000,
    monthly: [
      { month: "Jan", revenue: 45000 },
      { month: "Feb", revenue: 52000 },
      { month: "Mar", revenue: 48000 },
      { month: "Apr", revenue: 61000 },
      { month: "May", revenue: 58000 },
      { month: "Jun", revenue: 72000 },
      { month: "Jul", revenue: 125000 },
      { month: "Aug", revenue: 142000 },
      { month: "Sep", revenue: 98000 },
      { month: "Oct", revenue: 79000 },
      { month: "Nov", revenue: 88000 },
      { month: "Dec", revenue: 34000 },
    ],
    comparison: 12.5,
  },
  expenses: {
    total: 384000,
    breakdown: [
      { category: "Seeds", amount: 62000, color: "#22c55e" },
      { category: "Fertilizer", amount: 88000, color: "#f59e0b" },
      { category: "Labor", amount: 120000, color: "#3b82f6" },
      { category: "Equipment", amount: 74000, color: "#8b5cf6" },
      { category: "Water", amount: 40000, color: "#06b6d4" },
    ],
    comparison: -3.2,
  },
  profit: {
    netProfit: 508000,
    margin: 56.9,
    trend: [42000, 38000, 45000, 52000, 48000, 61000, 68000, 72000, 65000, 70000, 75000, 82000],
    trendDirection: "up",
  },
  yield: {
    total: 1280,
    perHectare: 28.3,
    cropWise: [
      { crop: "Rice", yield: 580, target: 600 },
      { crop: "Cotton", yield: 320, target: 350 },
      { crop: "Vegetables", yield: 380, target: 360 },
    ],
    target: 1310,
  },
  marketTrends: {
    marketName: "Khanna Mandi, Punjab",
    commodities: [
      { commodity: "Wheat", price: 2425, change: 2.3 },
      { commodity: "Rice", price: 3100, change: 1.8 },
      { commodity: "Maize", price: 1875, change: -0.6 },
      { commodity: "Cotton", price: 5620, change: 4.2 },
      { commodity: "Potato", price: 1280, change: -1.5 },
    ],
    priceHistory: [
      { day: "Mon", prices: [{ commodity: "Wheat", price: 2380 }, { commodity: "Rice", price: 3050 }, { commodity: "Cotton", price: 5450 }] },
      { day: "Tue", prices: [{ commodity: "Wheat", price: 2400 }, { commodity: "Rice", price: 3080 }, { commodity: "Cotton", price: 5520 }] },
      { day: "Wed", prices: [{ commodity: "Wheat", price: 2395 }, { commodity: "Rice", price: 3070 }, { commodity: "Cotton", price: 5580 }] },
      { day: "Thu", prices: [{ commodity: "Wheat", price: 2410 }, { commodity: "Rice", price: 3090 }, { commodity: "Cotton", price: 5550 }] },
      { day: "Fri", prices: [{ commodity: "Wheat", price: 2425 }, { commodity: "Rice", price: 3100 }, { commodity: "Cotton", price: 5620 }] },
    ],
    gainers: [
      { commodity: "Cotton", price: 5620, change: 4.2 },
      { commodity: "Wheat", price: 2425, change: 2.3 },
    ],
    losers: [
      { commodity: "Potato", price: 1280, change: -1.5 },
      { commodity: "Maize", price: 1875, change: -0.6 },
    ],
  },
  schemeRecommendations: [
    {
      id: "1",
      name: "PM-KISAN Samman Nidhi",
      description: "Income support of ₹6,000/year to farmer families",
      eligibility: "All small & marginal farmers with landholding up to 2 hectares",
      benefits: "₹6,000 per year in three equal installments",
    },
    {
      id: "2",
      name: "Pradhan Mantri Fasal Bima Yojana",
      description: "Comprehensive crop insurance against yield losses",
      eligibility: "All farmers growing notified crops in notified areas",
      benefits: "Low premium (2% Kharif, 1.5% Rabi crops) with govt subsidy",
    },
    {
      id: "3",
      name: "Soil Health Card Scheme",
      description: "Soil nutrient assessment and fertilizer recommendation",
      eligibility: "All farmers across India",
      benefits: "Free soil testing and customized fertilizer recommendations",
    },
  ],
};

// ---- Pagination ----

export const DEFAULT_PAGE_SIZE = 20;

export const TABLE_PAGE_SIZES = [10, 20, 50, 100] as const;

// ---- Debounce ----

export const DEBOUNCE_DELAYS = {
  search: 300,
  form: 500,
  resize: 200,
  scroll: 100,
} as const;
