"use client";

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  DollarSign,
  Activity,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const priceTrends = [
  { month: "Jan", Rice: 2850, Wheat: 2250, Cotton: 5400, Sugarcane: 350, Maize: 1850 },
  { month: "Feb", Rice: 2900, Wheat: 2280, Cotton: 5450, Sugarcane: 355, Maize: 1870 },
  { month: "Mar", Rice: 2950, Wheat: 2300, Cotton: 5500, Sugarcane: 360, Maize: 1880 },
  { month: "Apr", Rice: 3000, Wheat: 2320, Cotton: 5550, Sugarcane: 358, Maize: 1860 },
  { month: "May", Rice: 3050, Wheat: 2350, Cotton: 5480, Sugarcane: 352, Maize: 1840 },
  { month: "Jun", Rice: 3100, Wheat: 2380, Cotton: 5600, Sugarcane: 365, Maize: 1870 },
  { month: "Jul", Rice: 3080, Wheat: 2400, Cotton: 5650, Sugarcane: 370, Maize: 1900 },
  { month: "Aug", Rice: 3120, Wheat: 2425, Cotton: 5620, Sugarcane: 375, Maize: 1890 },
  { month: "Sep", Rice: 3150, Wheat: 2410, Cotton: 5700, Sugarcane: 372, Maize: 1910 },
  { month: "Oct", Rice: 3180, Wheat: 2390, Cotton: 5750, Sugarcane: 368, Maize: 1930 },
  { month: "Nov", Rice: 3200, Wheat: 2420, Cotton: 5800, Sugarcane: 374, Maize: 1950 },
  { month: "Dec", Rice: 3220, Wheat: 2450, Cotton: 5850, Sugarcane: 380, Maize: 1960 },
];

const heatmapData = [
  { commodity: "Rice", Jan: 2850, Feb: 2900, Mar: 2950, Apr: 3000, May: 3050, Jun: 3100, Jul: 3080, Aug: 3120, Sep: 3150, Oct: 3180, Nov: 3200, Dec: 3220 },
  { commodity: "Wheat", Jan: 2250, Feb: 2280, Mar: 2300, Apr: 2320, May: 2350, Jun: 2380, Jul: 2400, Aug: 2425, Sep: 2410, Oct: 2390, Nov: 2420, Dec: 2450 },
  { commodity: "Cotton", Jan: 5400, Feb: 5450, Mar: 5500, Apr: 5550, May: 5480, Jun: 5600, Jul: 5650, Aug: 5620, Sep: 5700, Oct: 5750, Nov: 5800, Dec: 5850 },
  { commodity: "Maize", Jan: 1850, Feb: 1870, Mar: 1880, Apr: 1860, May: 1840, Jun: 1870, Jul: 1900, Aug: 1890, Sep: 1910, Oct: 1930, Nov: 1950, Dec: 1960 },
  { commodity: "Sugarcane", Jan: 350, Feb: 355, Mar: 360, Apr: 358, May: 352, Jun: 365, Jul: 370, Aug: 375, Sep: 372, Oct: 368, Nov: 374, Dec: 380 },
];

const volumeTraded = [
  { month: "Jan", volume: 12500 },
  { month: "Feb", volume: 13200 },
  { month: "Mar", volume: 14800 },
  { month: "Apr", volume: 15200 },
  { month: "May", volume: 13800 },
  { month: "Jun", volume: 16500 },
  { month: "Jul", volume: 18200 },
  { month: "Aug", volume: 19500 },
  { month: "Sep", volume: 17800 },
  { month: "Oct", volume: 16200 },
  { month: "Nov", volume: 15500 },
  { month: "Dec", volume: 14200 },
];

const commodities = ["Rice", "Wheat", "Cotton", "Sugarcane", "Maize"] as const;
const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const getHeatColor = (value: number, min: number, max: number) => {
  const ratio = (value - min) / (max - min);
  if (ratio > 0.75) return "bg-emerald-500";
  if (ratio > 0.5) return "bg-emerald-400";
  if (ratio > 0.25) return "bg-emerald-300";
  return "bg-emerald-200";
};

const bestSellingTimes = [
  { commodity: "Rice", bestTime: "November - December", reason: "Post-harvest peak demand" },
  { commodity: "Wheat", bestTime: "March - April", reason: "Rabi harvest season" },
  { commodity: "Cotton", bestTime: "October - November", reason: "Ginning season demand" },
  { commodity: "Maize", bestTime: "August - September", reason: "Off-season supply gap" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload) return null;
  return (
    <div className="rounded-xl border border-border bg-card p-3 shadow-lg text-sm">
      <p className="font-medium text-foreground mb-1">{label}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} style={{ color: entry.color }} className="text-muted-foreground">
          {entry.name}: ₹{entry.value.toLocaleString("en-IN")}/qtl
        </p>
      ))}
    </div>
  );
};

export function MarketAnalytics() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: "Price Volatility Index", value: "8.2%", trend: "Low", icon: Activity, color: "text-emerald-500" },
          { label: "Top Gainers", value: "Cotton", sub: "+4.2%", icon: TrendingUp, color: "text-emerald-500" },
          { label: "Top Losers", value: "Maize", sub: "-1.5%", icon: TrendingDown, color: "text-red-500" },
          { label: "Total Volume", value: "1.85L tonnes", icon: BarChart3, color: "text-blue-500" },
        ].map(({ label, value, sub, trend, icon: Icon, color }) => (
          <Card key={label}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="text-lg font-bold mt-1">{value}</p>
                  {sub && <p className={cn("text-xs font-medium", trend === "Low" ? "text-emerald-500" : color)}>{sub}</p>}
                </div>
                <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg bg-card border border-border", color)}>
                  <Icon className="h-4 w-4" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Price Trends - Top 5 Commodities</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={priceTrends}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                <XAxis dataKey="month" className="text-xs text-muted-foreground" tickLine={false} />
                <YAxis className="text-xs text-muted-foreground" tickLine={false} tickFormatter={(v) => `₹${v}`} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line type="monotone" dataKey="Rice" stroke="#22c55e" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Wheat" stroke="#3b82f6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Cotton" stroke="#f59e0b" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Maize" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="Sugarcane" stroke="#06b6d4" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Price Heatmap - Commodity vs Month</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    <th className="text-left py-2 pr-4 text-muted-foreground font-medium">Commodity</th>
                    {months.map((m) => (
                      <th key={m} className="py-2 px-1 text-muted-foreground font-medium text-center">{m}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {heatmapData.map((row) => {
                    const values = months.map((m) => row[m as keyof typeof row] as number);
                    const min = Math.min(...values);
                    const max = Math.max(...values);
                    return (
                      <tr key={row.commodity}>
                        <td className="py-2 pr-4 font-medium text-foreground">{row.commodity}</td>
                        {months.map((m) => {
                          const val = row[m as keyof typeof row] as number;
                          const ratio = (val - min) / (max - min);
                          return (
                            <td key={m} className="py-1 px-1">
                              <div
                                className="rounded text-center py-1.5 text-[10px] font-mono text-white"
                                style={{
                                  backgroundColor: `rgba(34, 197, 94, ${0.2 + ratio * 0.8})`,
                                  color: ratio > 0.5 ? "white" : "hsl(var(--foreground))",
                                }}
                              >
                                ₹{val}
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Volume Traded</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={volumeTraded}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="month" className="text-xs text-muted-foreground" tickLine={false} />
                  <YAxis className="text-xs text-muted-foreground" tickLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}K`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="volume" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  <Line type="monotone" dataKey="volume" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Best Selling Times</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {bestSellingTimes.map((item) => (
                <div key={item.commodity} className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                  <TrendingUp className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">{item.commodity}</p>
                    <p className="text-xs text-emerald-500 font-medium">{item.bestTime}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{item.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Export / Import Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { commodity: "Rice", export: "+15%", import: "-2%", status: "export" },
                { commodity: "Wheat", export: "+8%", import: "+5%", status: "balanced" },
                { commodity: "Cotton", export: "+22%", import: "-8%", status: "export" },
                { commodity: "Maize", export: "-3%", import: "+12%", status: "import" },
                { commodity: "Sugarcane", export: "+10%", import: "0%", status: "export" },
              ].map((item) => (
                <div key={item.commodity} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      "w-2 h-2 rounded-full",
                      item.status === "export" ? "bg-emerald-500" : item.status === "import" ? "bg-red-500" : "bg-amber-500"
                    )} />
                    <span className="font-medium text-sm">{item.commodity}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono">
                    <span className="text-emerald-500">Exp: {item.export}</span>
                    <span className="text-red-500">Imp: {item.import}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
