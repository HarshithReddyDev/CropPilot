"use client";

import { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
  Legend,
} from "recharts";
import { Download, IndianRupee, TrendingUp, Calendar } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatCurrency, cn } from "@/lib/utils";

const monthlyRevenue = [
  { month: "Jan", current: 45000, previous: 38000 },
  { month: "Feb", current: 52000, previous: 42000 },
  { month: "Mar", current: 48000, previous: 44000 },
  { month: "Apr", current: 61000, previous: 50000 },
  { month: "May", current: 58000, previous: 52000 },
  { month: "Jun", current: 72000, previous: 58000 },
  { month: "Jul", current: 125000, previous: 98000 },
  { month: "Aug", current: 142000, previous: 110000 },
  { month: "Sep", current: 98000, previous: 85000 },
  { month: "Oct", current: 79000, previous: 72000 },
  { month: "Nov", current: 88000, previous: 75000 },
  { month: "Dec", current: 34000, previous: 28000 },
];

const revenueByCrop = [
  { name: "Rice", value: 385000, color: "#22c55e" },
  { name: "Wheat", value: 245000, color: "#3b82f6" },
  { name: "Cotton", value: 182000, color: "#f59e0b" },
  { name: "Sugarcane", value: 128000, color: "#8b5cf6" },
  { name: "Maize", value: 52000, color: "#06b6d4" },
];

const cumulativeRevenue = monthlyRevenue.reduce<{ month: string; cumulative: number }[]>((acc, curr) => {
  const prev = acc.length > 0 ? acc[acc.length - 1].cumulative : 0;
  acc.push({ month: curr.month, cumulative: prev + curr.current });
  return acc;
}, []);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-3 shadow-lg text-sm">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-muted-foreground">
          {entry.name}: {formatCurrency(entry.value)}
        </p>
      ))}
    </div>
  );
};

export function RevenueAnalytics() {
  const totalRevenue = useMemo(
    () => monthlyRevenue.reduce((sum, m) => sum + m.current, 0),
    []
  );
  const avgMonthly = Math.round(totalRevenue / 12);
  const growthRate = ((monthlyRevenue[11].current - monthlyRevenue[0].current) / monthlyRevenue[0].current * 100).toFixed(1);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Revenue", value: formatCurrency(totalRevenue), icon: IndianRupee, color: "text-emerald-500" },
          { label: "Avg Monthly", value: formatCurrency(avgMonthly), icon: Calendar, color: "text-blue-500" },
          { label: "Growth Rate", value: `${growthRate}%`, icon: TrendingUp, color: "text-amber-500" },
        ].map(({ label, value, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg bg-card border border-border", color)}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="text-lg font-bold">{value}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base">Monthly Revenue</CardTitle>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-1" />
            Report
          </Button>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={monthlyRevenue}>
                <defs>
                  <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="month" className="text-xs text-muted-foreground" tickLine={false} />
                <YAxis className="text-xs text-muted-foreground" tickLine={false} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}K`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="current" name="This Year" fill="#22c55e" radius={[4, 4, 0, 0]} />
                <Line
                  dataKey="previous"
                  name="Previous Year"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  strokeDasharray="4 4"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Revenue by Crop</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={revenueByCrop}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {revenueByCrop.map((entry) => (
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
            <CardTitle className="text-base">Cumulative Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={cumulativeRevenue}>
                  <defs>
                    <linearGradient id="cumGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="month" className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis className="text-xs text-muted-foreground" tickLine={false} tickFormatter={(v) => `₹${(v / 100000).toFixed(1)}L`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="cumulative"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fill="url(#cumGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
