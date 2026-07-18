import { apiGet } from "./api";
import type { WeatherRecord, WeatherForecast } from "@/types";

export async function getCurrentWeather(
  h3Index: string
): Promise<WeatherRecord> {
  return apiGet<WeatherRecord>(`/api/v1/weather/current/${h3Index}`);
}

export async function getForecast(
  h3Index: string,
  params?: { days?: number }
): Promise<WeatherForecast> {
  return apiGet<WeatherForecast>(`/api/v1/weather/forecast/${h3Index}`, {
    params: params as Record<string, string | number | boolean | undefined>,
  });
}
