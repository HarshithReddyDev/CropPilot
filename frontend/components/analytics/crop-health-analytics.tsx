"use client";

import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
  Legend,
} from "recharts";
import { AlertTriangle, Activity, Heart } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const healthMetrics = [
  { metric: "Leaf Color", value: 85, fullMark: 100 },
  { metric: "Stem Strength", value: 72, fullMark: 100 },
  { metric: "Pest Resistance", value: 68, fullMark: 100 },
  { metric: "Growth Rate", value: 90, fullMark: 100 },
  { metric: "Root Health", value: 78, fullMark: 100 },
];

const healthTrend = [
  { date: "Week 1", score: 82 },
  { date: "Week 2", score: 78 },
  { date: "Week 3", score: 75 },
  { date: "Week 4", score: 80 },
  { date: "Week 5", score: 72 },
  { date: "Week 6", score: 68 },
  { date: "Week 7", score: 74 },
  { date: "Week 8", score: 70 },
  { date: "Week 9", score: 76 },
  { date: "Week 10", score: 82 },
  { date: "Week 11", score: 85 },
  { date: "Week 12", score: 82 },
];

const healthByPlot = [
  { plot: "Plot A-1", crop: "Rice", health: 85 },
  { plot: "Plot A-2", crop: "Rice", health: 72 },
  { plot: "Plot A-3", crop: "Rice", health: 45 },
  { plot: "Plot B-1", crop: "Cotton", health: 78 },
  { plot: "Plot B-2", crop: "Cotton", health: 90 },
  { plot: "Plot C-1", crop: "Vegetables", health: 88 },
  { plot: "Plot C-2", crop: "Vegetables", health: 65 },
];

const alerts = [
  { date: "2 days ago", plot: "Plot A-3", issue: "Leaf Blight detected", severity: "high" },
  { date: "1 week ago", plot: "Plot B-1", issue: "Powdery Mildew", severity: "medium" },
  { date: "2 weeks ago", plot: "Plot C-2", issue: "Aphid Infestation", severity: "low" },
  { date: "3 weeks ago", plot: "Plot A-1", issue: "Root Rot detected", severity: "high" },
  { date: "1 month ago", plot: "Plot A-2", issue: "Nitrogen Deficiency", severity: "medium" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-3 shadow-lg text-sm">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-muted-foreground">
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
};

const getHealthColor = (score: number) => {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#f59e0b";
  return "#ef4444";
};

export function CropHealthAnalytics() {
  const overallScore = Math.round(
    healthMetrics.reduce((sum, m) => sum + m.value, 0) / healthMetrics.length
  );

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Overall Health</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            <div className="relative w-40 h-40">
              <svg className="w-full h-full" viewBox="0 0 120 120">
                <circle
                  cx="60" cy="60" r="54"
                  fill="none"
                  stroke="hsl(var(--muted))"
                  strokeWidth="8"
                />
                <circle
                  cx="60" cy="60" r="54"
                  fill="none"
                  stroke={getHealthColor(overallScore)}
                  strokeWidth="8"
                  strokeDasharray={`${(overallScore / 100) * 339.292} 339.292`}
                  strokeLinecap="round"
                  transform="rotate(-90 60 60)"
                  className="transition-all duration-1000"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <span className="text-3xl font-bold" style={{ color: getHealthColor(overallScore) }}>
                    {overallScore}
                  </span>
                  <span className="text-sm text-muted-foreground block">/100</span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-4">
              <Heart className="h-4 w-4 text-emerald-500" />
              <span className="text-sm text-muted-foreground">
                {overallScore >= 80 ? "Good condition" : overallScore >= 60 ? "Needs attention" : "Critical"}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Health Metrics Radar</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={healthMetrics}>
                  <PolarGrid className="stroke-border" />
                  <PolarAngleAxis dataKey="metric" className="text-xs text-muted-foreground" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} className="text-xs text-muted-foreground" />
                  <Radar
                    name="Health"
                    dataKey="value"
                    stroke="#22c55e"
                    fill="#22c55e"
                    fillOpacity={0.2}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Health Score Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={healthTrend}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="date" className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis domain={[40, 100]} className="text-xs text-muted-foreground" tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ fill: "#22c55e", r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Health by Plot</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={healthByPlot} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis type="number" domain={[0, 100]} className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis type="category" dataKey="plot" className="text-xs text-muted-foreground" tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="health" radius={[0, 4, 4, 0]}>
                    {healthByPlot.map((entry) => (
                      <Cell key={entry.plot} fill={getHealthColor(entry.health)} />
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
          <CardTitle className="text-base">Health Alerts Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-0">
            {alerts.map((alert, i) => (
              <div key={i} className="flex gap-4 pb-4 last:pb-0 relative">
                {i < alerts.length - 1 && (
                  <div className="absolute left-3 top-6 bottom-0 w-px bg-border" />
                )}
                <div className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5",
                  alert.severity === "high"
                    ? "bg-red-100 text-red-600 dark:bg-red-950/30"
                    : alert.severity === "medium"
                    ? "bg-amber-100 text-amber-600 dark:bg-amber-950/30"
                    : "bg-blue-100 text-blue-600 dark:bg-blue-950/30"
                )}>
                  <AlertTriangle className="h-3 w-3" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{alert.issue}</p>
                    <span className="text-xs text-muted-foreground">{alert.date}</span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">{alert.plot}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
