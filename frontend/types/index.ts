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
  market: string;
  district?: string;
  state: string;
  min_price: number;
  max_price: number;
  modal_price: number;
  price_per_unit: string;
  arrival_date: string;
  source: string;
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
