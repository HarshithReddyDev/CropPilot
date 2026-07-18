"use client";

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
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { FlaskConical, TrendingDown, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const npkUsage = [
  { month: "Jan", N: 40, P: 25, K: 20 },
  { month: "Feb", N: 42, P: 28, K: 22 },
  { month: "Mar", N: 38, P: 22, K: 18 },
  { month: "Apr", N: 45, P: 30, K: 25 },
  { month: "May", N: 50, P: 32, K: 28 },
  { month: "Jun", N: 48, P: 30, K: 26 },
  { month: "Jul", N: 52, P: 35, K: 30 },
  { month: "Aug", N: 55, P: 38, K: 32 },
  { month: "Sep", N: 51, P: 34, K: 28 },
  { month: "Oct", N: 48, P: 30, K: 25 },
  { month: "Nov", N: 45, P: 28, K: 22 },
  { month: "Dec", N: 42, P: 25, K: 20 },
];

const fertilizerBreakdown = [
  { name: "Urea (N)", value: 42, color: "#22c55e" },
  { name: "DAP (P)", value: 28, color: "#3b82f6" },
  { name: "MOP (K)", value: 18, color: "#f59e0b" },
  { name: "Compost", value: 12, color: "#8b5cf6" },
];

const costAnalysis = [
  { month: "Jan", cost: 8500, recommended: 8000 },
  { month: "Feb", cost: 9200, recommended: 8000 },
  { month: "Mar", cost: 7800, recommended: 8000 },
  { month: "Apr", cost: 10200, recommended: 9000 },
  { month: "May", cost: 11500, recommended: 9000 },
  { month: "Jun", cost: 10800, recommended: 9000 },
  { month: "Jul", cost: 12500, recommended: 10000 },
  { month: "Aug", cost: 13200, recommended: 10000 },
  { month: "Sep", cost: 11800, recommended: 10000 },
  { month: "Oct", cost: 10500, recommended: 9000 },
  { month: "Nov", cost: 9500, recommended: 8000 },
  { month: "Dec", cost: 8800, recommended: 8000 },
];

const efficiencyMetrics = [
  { metric: "N Use Efficiency", value: "68%", optimal: "75%", status: "warning" },
  { metric: "P Use Efficiency", value: "72%", optimal: "70%", status: "good" },
  { metric: "K Use Efficiency", value: "65%", optimal: "80%", status: "warning" },
  { metric: "Cost per kg Yield", value: "₹4.2/kg", optimal: "₹3.8/kg", status: "critical" },
];

const scheduleRecommendations = [
  { title: "Pre-Monsoon NPK Application", timing: "Apply before June 15", reason: "Aligns with Kharif sowing window" },
  { title: "Top Dressing for Rice", timing: "Apply in August", reason: "Peak tillering stage requires extra nitrogen" },
  { title: "Potash Boost for Cotton", timing: "Apply in September", reason: "Boll development stage needs increased K" },
  { title: "Zinc Supplementation", timing: "Apply in October", reason: "Corrects deficiency in vegetable plots" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-3 shadow-lg text-sm">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-muted-foreground">
          {entry.name}: {typeof entry.value === "number" ? `${entry.value} kg` : entry.value}
        </p>
      ))}
    </div>
  );
};

export function FertilizerAnalytics() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        {efficiencyMetrics.map((metric) => (
          <Card key={metric.metric}>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">{metric.metric}</p>
              <p className="text-lg font-bold mt-1">{metric.value}</p>
              <p className={cn(
                "text-[11px]",
                metric.status === "good" ? "text-emerald-500" : metric.status === "warning" ? "text-amber-500" : "text-red-500"
              )}>
                Optimal: {metric.optimal}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">N / P / K Usage Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={npkUsage}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="month" className="text-xs text-muted-foreground" tickLine={false} />
                <YAxis className="text-xs text-muted-foreground" tickLine={false} unit=" kg" />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="N" name="Nitrogen (N)" stackId="a" fill="#22c55e" radius={[0, 0, 0, 0]} />
                <Bar dataKey="P" name="Phosphorus (P)" stackId="a" fill="#3b82f6" />
                <Bar dataKey="K" name="Potassium (K)" stackId="a" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Fertilizer Type Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={fertilizerBreakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {fertilizerBreakdown.map((entry) => (
                      <Cell key={entry.name} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Cost Analysis vs Recommended</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={costAnalysis}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="month" className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis className="text-xs text-muted-foreground" tickLine={false} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="cost"
                    name="Actual Cost"
                    stroke="#ef4444"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="recommended"
                    name="Recommended"
                    stroke="#22c55e"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Schedule Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {scheduleRecommendations.map((rec) => (
              <div key={rec.title} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                <CheckCircle2 className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">{rec.title}</p>
                  <p className="text-xs text-emerald-500 font-medium">{rec.timing}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{rec.reason}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
