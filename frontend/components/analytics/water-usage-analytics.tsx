"use client";

import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Line,
  Cell,
  Legend,
} from "recharts";
import { Droplets, Zap, Lightbulb } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const dailyWaterUsage = [
  { day: "Mon", usage: 120, rainfall: 15, optimal: 100 },
  { day: "Tue", usage: 115, rainfall: 8, optimal: 100 },
  { day: "Wed", usage: 130, rainfall: 0, optimal: 100 },
  { day: "Thu", usage: 125, rainfall: 22, optimal: 100 },
  { day: "Fri", usage: 140, rainfall: 5, optimal: 100 },
  { day: "Sat", usage: 110, rainfall: 12, optimal: 100 },
  { day: "Sun", usage: 105, rainfall: 18, optimal: 100 },
];

const waterByCrop = [
  { crop: "Rice", usage: 450, color: "#22c55e" },
  { crop: "Sugarcane", usage: 380, color: "#3b82f6" },
  { crop: "Cotton", usage: 280, color: "#f59e0b" },
  { crop: "Wheat", usage: 220, color: "#8b5cf6" },
  { crop: "Maize", usage: 190, color: "#06b6d4" },
  { crop: "Vegetables", usage: 150, color: "#ec4899" },
];

const efficiencyMetrics = [
  { crop: "Rice", waterPerKg: 2.5, optimal: 2.8 },
  { crop: "Wheat", waterPerKg: 1.2, optimal: 1.5 },
  { crop: "Cotton", waterPerKg: 3.8, optimal: 4.0 },
  { crop: "Sugarcane", waterPerKg: 1.8, optimal: 2.0 },
  { crop: "Maize", waterPerKg: 1.5, optimal: 1.7 },
];

const savingsSuggestions = [
  { title: "Drip Irrigation for Cotton", saving: "25% water reduction", impact: "high" },
  { title: "Mulching in Vegetable Plots", saving: "18% water retention", impact: "medium" },
  { title: "Rainwater Harvesting", saving: "30% supplemental water", impact: "high" },
  { title: "Scheduled Irrigation Timing", saving: "15% efficiency gain", impact: "medium" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-3 shadow-lg text-sm">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-muted-foreground">
          {entry.name}: {entry.name === "Rainfall" ? `${entry.value} mm` : `${entry.value} L`}
        </p>
      ))}
    </div>
  );
};

export function WaterUsageAnalytics() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Usage", value: "845,000 L", sub: "This week", icon: Droplets, color: "text-blue-500" },
          { label: "Efficiency", value: "84%", sub: "vs optimal", icon: Zap, color: "text-emerald-500" },
          { label: "Rainfall", value: "80 mm", sub: "This week", icon: Droplets, color: "text-cyan-500" },
        ].map(({ label, value, sub, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg bg-card border border-border", color)}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="text-lg font-bold">{value}</p>
                  <p className="text-[11px] text-muted-foreground">{sub}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Daily Water Usage with Rainfall</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={dailyWaterUsage}>
                <defs>
                  <linearGradient id="waterGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="day" className="text-xs text-muted-foreground" tickLine={false} />
                <YAxis className="text-xs text-muted-foreground" tickLine={false} unit=" L" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="usage"
                  name="Water Usage"
                  stroke="#3b82f6"
                  fill="url(#waterGrad)"
                  strokeWidth={2}
                />
                <Bar dataKey="rainfall" name="Rainfall" fill="#06b6d4" radius={[4, 4, 0, 0]} opacity={0.6} />
                <Line
                  type="monotone"
                  dataKey="optimal"
                  name="Optimal Range"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  strokeDasharray="6 3"
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Water Usage by Crop</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={waterByCrop} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis type="number" className="text-xs text-muted-foreground" tickLine={false} unit=" L" />
                  <YAxis type="category" dataKey="crop" className="text-xs text-muted-foreground" tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="usage" radius={[0, 4, 4, 0]}>
                    {waterByCrop.map((entry) => (
                      <Cell key={entry.crop} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Water Efficiency (L per kg yield)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={efficiencyMetrics} barGap={8}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="crop" className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis className="text-xs text-muted-foreground" tickLine={false} unit=" L" />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Bar dataKey="waterPerKg" name="Current" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="optimal" name="Optimal" fill="#22c55e" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Water Savings Suggestions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {savingsSuggestions.map((suggestion) => (
              <div
                key={suggestion.title}
                className="flex items-start gap-3 p-3 rounded-lg bg-muted/50"
              >
                <Lightbulb className={cn(
                  "h-5 w-5 shrink-0 mt-0.5",
                  suggestion.impact === "high" ? "text-emerald-500" : "text-amber-500"
                )} />
                <div>
                  <p className="text-sm font-medium">{suggestion.title}</p>
                  <p className="text-xs text-muted-foreground">{suggestion.saving}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
