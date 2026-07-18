"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Search, MapPin, ChevronDown } from "lucide-react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { CurrentWeather } from "@/components/weather/current-weather";
import { HourlyForecast } from "@/components/weather/hourly-forecast";
import { WeeklyForecast } from "@/components/weather/weekly-forecast";
import { WeatherDetails } from "@/components/weather/weather-details";
import { WeatherMap } from "@/components/weather/weather-map";
import { cn } from "@/lib/utils";

const LOCATIONS = [
  "New Delhi, Delhi",
  "Lucknow, Uttar Pradesh",
  "Patna, Bihar",
  "Nagpur, Maharashtra",
  "Hyderabad, Telangana",
  "Bangalore, Karnataka",
  "Chennai, Tamil Nadu",
  "Kolkata, West Bengal",
  "Ahmedabad, Gujarat",
  "Jaipur, Rajasthan",
];

function generateHourlyForecast() {
  const now = new Date();
  const hours: { time: string; temp: number; condition: string; rainProbability: number; isCurrent?: boolean }[] = [];

  const conditions = [
    "Sunny", "Clear", "Partly Cloudy", "Cloudy",
    "Light Rain", "Moderate Rain", "Overcast", "Hazy",
  ];

  for (let i = 0; i < 24; i++) {
    const h = new Date(now.getTime() + i * 3600000);
    const isCurrent = i === 0;
    const timeStr = h.toLocaleTimeString("en-US", { hour: "numeric", hour12: true });

    const baseTemp = 28 + Math.sin((h.getHours() - 6) * (Math.PI / 12)) * 8;
    const temp = Math.round(baseTemp + (Math.random() - 0.5) * 4);
    const condition = conditions[Math.floor(Math.random() * conditions.length)];
    const rainProb = Math.max(0, Math.min(100, Math.round(Math.random() * 60 - (temp > 32 ? 10 : 0) + 20)));

    hours.push({
      time: timeStr,
      temp,
      condition,
      rainProbability: rainProb,
      isCurrent,
    });
  }
  return hours;
}

function generateWeeklyForecast() {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const conditions = [
    "Sunny", "Partly Cloudy", "Cloudy", "Light Rain",
    "Thunderstorm", "Clear", "Hazy", "Moderate Rain",
  ];
  const today = new Date();

  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() + i);
    const baseHigh = 30 + Math.sin((d.getDate() % 10) * 0.5) * 5;
    const baseLow = baseHigh - 4 - Math.random() * 4;

    return {
      day: days[d.getDay()],
      date: d.toLocaleDateString("en-IN", { day: "numeric", month: "short" }),
      high: Math.round(baseHigh + (Math.random() - 0.5) * 4),
      low: Math.round(baseLow + (Math.random() - 0.5) * 2),
      condition: conditions[Math.floor(Math.random() * conditions.length)],
      rainProbability: Math.round(Math.random() * 80),
      windSpeed: Math.round(5 + Math.random() * 25),
      isToday: i === 0,
    };
  });
}

const MOCK_WEATHER = {
  location: "New Delhi, Delhi",
  date: new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }),
  temperature: 34,
  feelsLike: 36,
  high: 38,
  low: 26,
  description: "Partly cloudy with heat wave conditions",
  humidity: 52,
  condition: "sunny" as const,
  rainProbability: 15,
  windSpeed: 12,
  windDirection: 280,
  uvIndex: 7,
  pressure: 1008,
  visibility: 6,
  hourly: generateHourlyForecast(),
  weekly: generateWeeklyForecast(),
};

export default function WeatherPage() {
  const [searchOpen, setSearchOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedLocation, setSelectedLocation] = useState(MOCK_WEATHER.location);

  const filtered = LOCATIONS.filter((l) =>
    l.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelectLocation = (loc: string) => {
    setSelectedLocation(loc);
    setSearchOpen(false);
    setSearch("");
  };

  const weather = {
    ...MOCK_WEATHER,
    location: selectedLocation,
  };

  return (
    <DashboardLayout>
      <div className="mx-auto max-w-7xl space-y-6">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Weather
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Real-time weather data and forecasts for your farm
            </p>
          </div>

          <div className="relative">
            <button
              onClick={() => setSearchOpen(!searchOpen)}
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-4 py-2.5 text-sm font-medium text-foreground transition-all hover:bg-accent min-w-[200px]"
            >
              <MapPin className="h-4 w-4 text-primary" />
              <span className="flex-1 text-left truncate">{selectedLocation}</span>
              <ChevronDown
                className={cn(
                  "h-4 w-4 text-muted-foreground transition-transform",
                  searchOpen && "rotate-180"
                )}
              />
            </button>

            {searchOpen && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="absolute right-0 top-full z-50 mt-2 w-72 overflow-hidden rounded-xl border border-border bg-card shadow-xl"
              >
                <div className="border-b border-border p-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <input
                      value={search}
                      onChange={(e) => setSearch(e.target.value)}
                      placeholder="Search location..."
                      className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-sm outline-none ring-1 ring-transparent transition-all placeholder:text-muted-foreground focus:ring-primary"
                    />
                  </div>
                </div>
                <div className="max-h-60 overflow-y-auto p-2">
                  {filtered.length === 0 ? (
                    <p className="p-3 text-center text-sm text-muted-foreground">
                      No locations found
                    </p>
                  ) : (
                    filtered.map((loc) => (
                      <button
                        key={loc}
                        onClick={() => handleSelectLocation(loc)}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors",
                          loc === selectedLocation
                            ? "bg-primary/10 text-primary"
                            : "text-foreground hover:bg-muted"
                        )}
                      >
                        <MapPin className="h-4 w-4 shrink-0 text-muted-foreground" />
                        {loc}
                      </button>
                    ))
                  )}
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-7">
          <div className="lg:col-span-4">
            <CurrentWeather
              location={weather.location}
              date={weather.date}
              temperature={weather.temperature}
              feelsLike={weather.feelsLike}
              high={weather.high}
              low={weather.low}
              description={weather.description}
              humidity={weather.humidity}
              condition={weather.condition}
            />
          </div>
          <div className="lg:col-span-3">
            <WeatherDetails
              rainProbability={weather.rainProbability}
              windSpeed={weather.windSpeed}
              windDirection={weather.windDirection}
              humidity={weather.humidity}
              uvIndex={weather.uvIndex}
              pressure={weather.pressure}
              visibility={weather.visibility}
            />
          </div>
        </div>

        <HourlyForecast data={weather.hourly} />

        <div className="grid gap-6 lg:grid-cols-7">
          <div className="lg:col-span-4">
            <WeeklyForecast data={weather.weekly} />
          </div>
          <div className="lg:col-span-3">
            <WeatherMap
              center={{ lat: 28.6139, lng: 77.209 }}
              locationName={weather.location}
            />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
