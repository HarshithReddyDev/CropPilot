"use client";

import { useState, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
  Cell,
} from "recharts";
import { Filter, ArrowUp, ArrowDown } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

const seasons = ["Kharif 2025", "Rabi 2024-25", "Kharif 2024", "Rabi 2023-24"];

const yieldPerCropSeason = [
  { crop: "Rice", "Kharif 2025": 4.2, "Rabi 2024-25": 3.8, "Kharif 2024": 3.9, "Rabi 2023-24": 3.5 },
  { crop: "Wheat", "Kharif 2025": 3.1, "Rabi 2024-25": 4.5, "Kharif 2024": 2.8, "Rabi 2023-24": 4.1 },
  { crop: "Cotton", "Kharif 2025": 2.8, "Rabi 2024-25": 2.2, "Kharif 2024": 2.5, "Rabi 2023-24": 2.0 },
  { crop: "Sugarcane", "Kharif 2025": 65.0, "Rabi 2024-25": 62.0, "Kharif 2024": 60.0, "Rabi 2023-24": 58.0 },
  { crop: "Maize", "Kharif 2025": 3.5, "Rabi 2024-25": 3.0, "Kharif 2024": 3.2, "Rabi 2023-24": 2.8 },
];

const yieldTrend = [
  { year: "2020", yield: 2.8 },
  { year: "2021", yield: 3.1 },
  { year: "2022", yield: 3.4 },
  { year: "2023", yield: 3.6 },
  { year: "2024", yield: 3.9 },
  { year: "2025", yield: 4.2 },
];

const yieldVsTarget = [
  { crop: "Rice", actual: 4.2, target: 4.5 },
  { crop: "Wheat", actual: 3.1, target: 3.5 },
  { crop: "Cotton", actual: 2.8, target: 3.0 },
  { crop: "Sugarcane", actual: 65.0, target: 70.0 },
  { crop: "Maize", actual: 3.5, target: 3.2 },
];

const yieldPerHectare = [
  { crop: "Rice", yield: 4.2, color: "#22c55e" },
  { crop: "Wheat", yield: 3.1, color: "#3b82f6" },
  { crop: "Cotton", yield: 2.8, color: "#f59e0b" },
  { crop: "Sugarcane", yield: 65.0, color: "#8b5cf6" },
  { crop: "Maize", yield: 3.5, color: "#06b6d4" },
];

const topCrops = [
  { name: "Sugarcane", yield: 65.0, change: 5.2 },
  { name: "Rice", yield: 4.2, change: 8.1 },
  { name: "Maize", yield: 3.5, change: 9.4 },
  { name: "Wheat", yield: 3.1, change: -2.3 },
  { name: "Cotton", yield: 2.8, change: 12.0 },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-3 shadow-lg text-sm">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-muted-foreground">
          {entry.name}: {entry.value} t/ha
        </p>
      ))}
    </div>
  );
};

export function YieldAnalytics() {
  const [selectedSeason, setSelectedSeason] = useState(seasons[0]);

  const sortedCrops = useMemo(
    () => [...topCrops].sort((a, b) => b.yield - a.yield),
    []
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Select value={selectedSeason} onValueChange={setSelectedSeason}>
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {seasons.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-emerald-500" /> Current</span>
          <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-blue-500" /> Target</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Yield per Crop - {selectedSeason}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={yieldPerCropSeason} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="crop" className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis className="text-xs text-muted-foreground" tickLine={false} unit=" t" />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey={seasons[0]} name="Kharif 2025" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  <Bar dataKey={seasons[1]} name="Rabi 2024-25" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey={seasons[2]} name="Kharif 2024" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Yield Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={yieldTrend}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="year" className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis className="text-xs text-muted-foreground" tickLine={false} unit=" t/ha" />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="yield"
                    stroke="#22c55e"
                    strokeWidth={3}
                    dot={{ fill: "#22c55e", strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Yield vs Target</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={yieldVsTarget} barGap={8}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="crop" className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis className="text-xs text-muted-foreground" tickLine={false} unit=" t" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="actual" name="Actual" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="target" name="Target" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Yield per Hectare</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={yieldPerHectare} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis type="number" className="text-xs text-muted-foreground" tickLine={false} unit=" t" />
                  <YAxis type="category" dataKey="crop" className="text-xs text-muted-foreground" tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="yield" radius={[0, 4, 4, 0]}>
                    {yieldPerHectare.map((entry) => (
                      <Cell key={entry.crop} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Top & Bottom Performing Crops</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {sortedCrops.map((crop, i) => (
              <div
                key={crop.name}
                className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
              >
                <div className="flex items-center gap-3">
                  <span className={cn(
                    "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white",
                    i === 0 ? "bg-emerald-500" : i === sortedCrops.length - 1 ? "bg-red-500" : "bg-muted-foreground"
                  )}>
                    {i + 1}
                  </span>
                  <span className="font-medium">{crop.name}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="font-mono text-sm">{crop.yield} t/ha</span>
                  <span className={cn(
                    "flex items-center gap-1 text-xs font-medium",
                    crop.change >= 0 ? "text-emerald-500" : "text-red-500"
                  )}>
                    {crop.change >= 0 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                    {Math.abs(crop.change)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
