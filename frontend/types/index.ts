export interface User {
  id: string;
  email: string;
  phone?: string;
  full_name: string;
  role: "farmer" | "analyst" | "admin";
  state?: string;
  district?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Farm {
  id: string;
  farmer_id: string;
  name: string;
  description?: string;
  address?: string;
  city?: string;
  state?: string;
  country: string;
  total_area_hectares: number;
  soil_type?: string;
  irrigation_type?: string;
  created_at: string;
  plots?: Plot[];
}

export interface Plot {
  id: string;
  farm_id: string;
  farmer_id: string;
  name: string;
  crop_type?: string;
  crop_variety?: string;
  sowing_date?: string;
  expected_harvest_date?: string;
  area_hectares: number;
  h3_index: string;
  h3_resolution: number;
  soil_ph?: number;
  soil_moisture?: number;
  irrigation_type?: string;
  status: string;
  geometry?: GeoJSON.Polygon;
  centroid?: GeoJSON.Point;
  created_at: string;
}

export interface DiseaseLog {
  id: string;
  plot_id: string;
  farmer_id: string;
  h3_spatial_index: string;
  detected_disease?: string;
  confidence: number;
  detections: Detection[];
  image_url?: string;
  severity: string;
  recommendation?: string;
  is_resolved: boolean;
  created_at: string;
  detections_rel?: DiseaseDetection[];
}

export interface DiseaseDetection {
  id: string;
  disease_log_id: string;
  class_name: string;
  confidence: number;
  bbox?: BBox;
  created_at: string;
}

export interface Detection {
  class_name: string;
  confidence: number;
  bbox?: BBox;
}

export interface BBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface WeatherRecord {
  id: string;
  plot_id?: string;
  h3_index: string;
  temperature?: number;
  feels_like?: number;
  humidity?: number;
  pressure?: number;
  wind_speed?: number;
  wind_deg?: number;
  weather_main?: string;
  weather_description?: string;
  recorded_at: string;
}

export interface WeatherForecast {
  id: string;
  h3_index: string;
  forecast_data: ForecastDay[];
  forecasted_at: string;
}

export interface ForecastDay {
  date: string;
  temp_max: number;
  temp_min: number;
  humidity: number;
  wind_speed: number;
  weather_main: string;
  weather_description: string;
  rain_probability: number;
}

export interface MarketPrice {
  id: string;
  commodity: string;
  variety?: string;
  grade?: string;
  market: string;
  district?: string;
  state: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  price_per_unit: string;
  arrival_date: string;
  arrivals?: number | null;
  arrival_unit?: string | null;
  source: string;
  source_resource_id?: string;
  fetched_at?: string;
  ingested_at?: string;
}

export interface MarketProvenance {
  name: string;
  resource_id: string;
  retrieved_at: string;
}

export interface MarketFreshness {
  latest_observation_date?: string;
  oldest_observation_date?: string;
  age_days?: number;
  is_stale: boolean;
  observation_count: number;
}

export interface LatestPricesResponse {
  items: MarketPrice[];
  provenance: MarketProvenance;
  freshness: MarketFreshness;
}

export interface MarketHistoryPoint {
  arrival_date: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  market: string;
  variety?: string;
  grade?: string;
  price_per_unit: string;
  arrivals?: number | null;
  arrival_unit?: string | null;
}

export interface MarketHistoryStats {
  point_count: number;
  first_modal_price?: number;
  last_modal_price?: number;
  change?: number;
  change_percent?: number;
  min_modal_price?: number;
  max_modal_price?: number;
}

export interface MarketHistoryResponse {
  points: MarketHistoryPoint[];
  stats: MarketHistoryStats;
  provenance: MarketProvenance;
  freshness: MarketFreshness;
}

export interface MarketComparisonRow {
  market: string;
  district?: string;
  state: string;
  commodity: string;
  variety?: string;
  grade?: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  price_per_unit: string;
  arrival_date: string;
  arrivals?: number | null;
  arrival_unit?: string | null;
  source: string;
}

export interface MarketComparisonResponse {
  rows: MarketComparisonRow[];
  group: Record<string, string>;
  provenance: MarketProvenance;
  freshness: MarketFreshness;
}

export interface MarketMetaResponse {
  values: string[];
  provenance: MarketProvenance;
}

export interface MarketOverview {
  states_reporting: number;
  markets_reporting: number;
  commodities_reported: number;
  oldest_observation_date?: string;
  latest_observation_date?: string;
  provenance: MarketProvenance;
}

export interface GovernmentScheme {
  id: string;
  scheme_name: string;
  scheme_code?: string;
  description: string;
  ministry?: string;
  department?: string;
  state_jurisdiction?: string;
  eligibility_criteria?: string;
  benefits?: string;
  application_process?: string;
  documents_required?: string;
  funding_pattern?: string;
  beneficiary_type?: string;
  category?: string;
  tags: string[];
  is_active: boolean;
  website_url?: string;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  body: string;
  notification_type: "info" | "alert" | "warning" | "success";
  channel: string;
  reference_type?: string;
  reference_id?: string;
  is_read: boolean;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  sources?: Source[];
}

export interface Source {
  title: string;
  content: string;
  score?: number;
}

export interface AnalyticsData {
  revenue: number[];
  yield: number[];
  crop_health: number;
  water_usage: number[];
  fertilizer_usage: number[];
  dates: string[];
}

export interface H3HexFeature {
  h3_index: string;
  confidence: number;
  crop_type?: string;
  color?: [number, number, number, number];
}

export interface MarketDataSource {
  code: string;
  name: string;
  organization: string;
  category: string;
  base_url: string;
  source_type: string;
  access_type: string;
  attribution_text: string;
  enabled: boolean;
  status: string;
  provides: string[];
}

export interface MandiObservation extends MarketPrice {
  source_code: string;
}

export interface EnamTradeObservation {
  id: string;
  market: string;
  commodity: string;
  variety?: string;
  grade?: string;
  quantity?: number;
  price?: number;
  unit: string;
  trade_date: string;
  trade_type: string;
  source: string;
}

export interface ConsumerPriceObservation {
  id: string;
  centre: string;
  commodity: string;
  price_type: string;
  price: number;
  unit: string;
  observation_date: string;
  source: string;
}

export interface AgriculturalPriceSeries {
  id: string;
  series: string;
  commodity: string;
  geography: string;
  price?: number;
  unit: string;
  observation_date: string;
  source: string;
}

export interface TradeObservation {
  id: string;
  commodity: string;
  hs_code: string;
  country: string;
  region: string;
  trade_type: string;
  month: string;
  quantity?: number;
  quantity_unit: string;
  value?: number;
  value_unit: string;
  source: string;
}

export interface ExchangeObservation {
  id: string;
  instrument: string;
  commodity: string;
  contract: string;
  expiry?: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
  ltp?: number;
  volume?: number;
  open_interest?: number;
  unit: string;
  observation_date: string;
  source: string;
}
