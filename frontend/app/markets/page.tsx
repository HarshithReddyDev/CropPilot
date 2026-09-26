"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { PriceTable } from "@/components/markets/price-table";
// recharts is the heaviest dep on this route: split it into its own chunk
// so the filter UI + price table paint without parsing chart code first.
const PriceHistoryChart = dynamic(
  () => import("@/components/markets/price-history-chart").then((m) => m.PriceHistoryChart),
  { ssr: false, loading: () => <PanelSkeleton /> },
);
import { MarketComparison } from "@/components/markets/market-comparison";
import { FreshnessBadge } from "@/components/markets/freshness-badge";
import { SourceAttribution } from "@/components/markets/source-attribution";
import {
  useMarketCommodities,
  useMarketDistricts,
  useMarketGrades,
  useMarketMarkets,
  useMarketStates,
  useMarketVarieties,
  useMarketsComparison,
  useMarketsEnabled,
  useMarketsHistory,
  useMarketsLatest,
  useMarketsOverview,
} from "@/hooks/use-market-intelligence";
import { useAuthReady } from "@/hooks/use-auth-ready";
import { ApiError } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SearchableSelect } from "@/components/markets/searchable-select";
import { cn } from "@/lib/utils";

const WINDOWS = [7, 30, 90] as const;
const ALL = "all";

import { useTranslation } from "@/lib/i18n";

function PanelSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-card p-4">
      <div className="h-4 w-40 animate-pulse rounded bg-muted" />
      <div className="mt-4 space-y-2">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-8 animate-pulse rounded bg-muted/60" />
        ))}
      </div>
    </div>
  );
}

function ErrorPanel({
  message,
  onRetry,
  title,
}: {
  message: string;
  onRetry: () => void;
  title?: string;
}) {
  const { t } = useTranslation();
  return (
    <div className="rounded-xl border border-border bg-card p-6 text-center">
      <p className="text-sm font-medium text-foreground">{title ?? t("markets.unavailableTitle")}</p>
      <p className="mx-auto mt-1 max-w-md text-xs text-muted-foreground">{message}</p>
      <button
        onClick={onRetry}
        className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:opacity-90"
      >
        {t("markets.tryAgain")}
      </button>
    </div>
  );
}

function SignInPanel() {
  const { t } = useTranslation();
  return (
    <div className="rounded-xl border border-border bg-card p-6 text-center">
      <p className="text-sm font-medium text-foreground">{t("markets.signInRequired")}</p>
      <p className="mx-auto mt-1 max-w-md text-xs text-muted-foreground">
        {t("markets.signInPrompt")}
      </p>
      <a
        href="/auth/login"
        className="mt-4 inline-block rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:opacity-90"
      >
        {t("auth.signIn")}
      </a>
    </div>
  );
}

function isAuthError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

function friendlyError(t: (key: string) => string, error: unknown): string {
  if (error instanceof Error) {
    if (error.message.includes("401")) {
      return t("markets.signInNeeded");
    }
    if (error.message.toLowerCase().includes("network") || error.message.includes("Failed to fetch")) {
      return t("markets.offline");
    }
    return t("markets.loadError");
  }
  return t("markets.loadErrorShort");
}

function opt(value: string): string | undefined {
  return value === ALL || value === "" ? undefined : value;
}

export default function MarketsPage() {
  const { t } = useTranslation();
  const authReady = useAuthReady();
  const marketsEnabled = useMarketsEnabled();
  const profileState = useAuthStore((s) => s.user?.state);
  // Assistant deep-link: ?state=&district=&market=&commodity=&variety=&grade=
  // pre-fills filters (semantic UI action `apply-market-filters`).
  const initialParams = useMemo(() => {
    if (typeof window === "undefined") return new URLSearchParams();
    return new URLSearchParams(window.location.search);
  }, []);
  const param = (key: string, fallback: string) => initialParams.get(key) ?? fallback;

  const [state, setState] = useState<string>(() => param("state", ""));
  const [district, setDistrict] = useState<string>(() => param("district", ALL));
  const [market, setMarket] = useState<string>(() => param("market", ALL));
  const [commodity, setCommodity] = useState<string>(() => param("commodity", ""));
  const [variety, setVariety] = useState<string>(() => param("variety", ALL));
  const [grade, setGrade] = useState<string>(() => param("grade", ALL));
  const [days, setDays] = useState<(typeof WINDOWS)[number]>(30);

  // Preselect the signed-in farmer's profile state when available.
  // Otherwise the page starts at national scope once a state is chosen.
  useEffect(() => {
    if (!state && profileState) {
      setState(profileState);
    }
  }, [state, profileState]);

  const statesQuery = useMarketStates();
  const districtsQuery = useMarketDistricts(opt(state));
  const marketsQuery = useMarketMarkets({
    state: opt(state),
    district: opt(district),
    commodity: commodity || undefined,
  });
  const commoditiesQuery = useMarketCommodities({
    state: opt(state),
    district: opt(district),
    market: opt(market),
  });
  const varietiesQuery = useMarketVarieties({
    state: opt(state),
    district: opt(district),
    market: opt(market),
    commodity: commodity || undefined,
  });
  const gradesQuery = useMarketGrades({
    state: opt(state),
    district: opt(district),
    market: opt(market),
    commodity: commodity || undefined,
    variety: opt(variety),
  });
  const overviewQuery = useMarketsOverview(opt(state));

  const stateList = useMemo(() => statesQuery.data?.values ?? [], [statesQuery.data]);
  const districtList = useMemo(() => districtsQuery.data?.values ?? [], [districtsQuery.data]);
  const marketList = useMemo(() => marketsQuery.data?.values ?? [], [marketsQuery.data]);
  const commodityList = useMemo(
    () => commoditiesQuery.data?.values ?? [],
    [commoditiesQuery.data]
  );
  const varietyList = useMemo(() => varietiesQuery.data?.values ?? [], [varietiesQuery.data]);
  const gradeList = useMemo(() => gradesQuery.data?.values ?? [], [gradesQuery.data]);

  useEffect(() => {
    if (!commodity && commodityList.length > 0) {
      setCommodity(commodityList[0]);
    }
  }, [commodity, commodityList]);

  const latestQuery = useMarketsLatest({
    state: opt(state),
    district: opt(district),
    commodity: commodity || undefined,
    market: opt(market),
    variety: opt(variety),
    grade: opt(grade),
    limit: 100,
  });

  const historyQuery = useMarketsHistory(
    commodity
      ? {
          commodity,
          state: opt(state),
          district: opt(district),
          market: opt(market),
          variety: opt(variety),
          grade: opt(grade),
          days,
        }
      : null
  );

  const comparisonQuery = useMarketsComparison(
    commodity
      ? {
          commodity,
          state: opt(state),
          district: opt(district),
          variety: opt(variety),
          grade: opt(grade),
        }
      : null
  );

  const onStateChange = (v: string) => {
    setState(v === ALL ? "" : v);
    setDistrict(ALL);
    setMarket(ALL);
    setVariety(ALL);
    setGrade(ALL);
  };

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-foreground">{t("markets.title")}</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {t("markets.subtitle")}
            </p>
          </div>
          {latestQuery.data && <FreshnessBadge freshness={latestQuery.data.freshness} />}
        </div>

        {overviewQuery.data && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              { key: "markets.statesReporting", value: String(overviewQuery.data.states_reporting) },
              { key: "markets.marketsReporting", value: String(overviewQuery.data.markets_reporting) },
              { key: "markets.commoditiesReported", value: String(overviewQuery.data.commodities_reported) },
              { key: "markets.latestObservation", value: overviewQuery.data.latest_observation_date ?? "--" },
            ].map(({ key, value }) => (
              <div key={key} className="rounded-xl border border-border bg-card p-3">
                <p className="text-xs text-muted-foreground">{t(key)}</p>
                <p className="mt-1 text-lg font-semibold text-foreground">{value}</p>
              </div>
            ))}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <SearchableSelect
            value={state === "" ? ALL : state}
            onChange={onStateChange}
            options={stateList}
            placeholder={t("markets.allStates")}
            searchPlaceholder={t("markets.searchStates")}
            emptyText={t("markets.noMatchState")}
          />

          <SearchableSelect
            value={district}
            onChange={(v) => {
              setDistrict(v);
              setMarket(ALL);
            }}
            options={districtList}
            placeholder={state ? t("markets.allDistricts") : t("markets.selectStateFirst")}
            searchPlaceholder={t("markets.searchDistricts")}
            emptyText={t("markets.noMatchDistrict")}
            disabled={!state}
          />

          <SearchableSelect
            value={market}
            onChange={setMarket}
            options={marketList}
            placeholder={state ? t("markets.allMarkets") : t("markets.selectStateFirst")}
            searchPlaceholder={t("markets.searchMarkets")}
            emptyText={t("markets.noMatchMarket")}
            disabled={!state}
          />

          <Select
            value={commodity}
            onValueChange={(v) => {
              setCommodity(v);
              setMarket(ALL);
              setVariety(ALL);
              setGrade(ALL);
            }}
          >
            <SelectTrigger className="h-9 w-48">
              <SelectValue placeholder={t("markets.selectCommodity")} />
            </SelectTrigger>
            <SelectContent>
              {commodityList.map((c: string) => (
                <SelectItem key={c} value={c}>{c}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={variety} onValueChange={setVariety} disabled={!commodity}>
            <SelectTrigger className="h-9 w-40">
              <SelectValue placeholder={t("markets.allVarieties")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>{t("markets.allVarieties")}</SelectItem>
              {varietyList.map((v: string) => (
                <SelectItem key={v} value={v}>{v}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={grade} onValueChange={setGrade} disabled={!commodity}>
            <SelectTrigger className="h-9 w-40">
              <SelectValue placeholder={t("markets.allGrades")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>{t("markets.allGrades")}</SelectItem>
              {gradeList.map((g: string) => (
                <SelectItem key={g} value={g}>{g}</SelectItem>
              ))}
            </SelectContent>
          </Select>

          <div className="flex gap-1 rounded-lg bg-muted p-0.5">
            {WINDOWS.map((w) => (
              <button
                key={w}
                onClick={() => setDays(w)}
                className={cn(
                  "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                  days === w
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {w}d
              </button>
            ))}
          </div>
        </div>

        {latestQuery.data?.freshness.is_stale && (
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
            <p className="text-sm font-medium text-foreground">{t("markets.storedObservations")}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {t("markets.storedObservationsBody")}
            </p>
          </div>
        )}

        {!authReady ? (
          <PanelSkeleton />
        ) : !marketsEnabled ? (
          <SignInPanel />
        ) : latestQuery.isLoading ? (
          <PanelSkeleton />
        ) : latestQuery.isError ? (
          isAuthError(latestQuery.error) ? (
            <SignInPanel />
          ) : (
            <ErrorPanel message={friendlyError(t, latestQuery.error)} onRetry={() => latestQuery.refetch()} />
          )
        ) : (latestQuery.data?.items.length ?? 0) === 0 ? (
          <div className="rounded-xl border border-border bg-card p-6 text-center">
            <p className="text-sm font-medium text-foreground">{t("markets.noRecentPrice")}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {t("markets.emptyHint")}
            </p>
          </div>
        ) : (
          <PriceTable data={latestQuery.data?.items ?? []} showState={!state} />
        )}

        {commodity && marketsEnabled && (
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              {historyQuery.isLoading ? (
                <PanelSkeleton />
              ) : historyQuery.isError ? (
                isAuthError(historyQuery.error) ? (
                  <SignInPanel />
                ) : (
                  <ErrorPanel message={friendlyError(t, historyQuery.error)} onRetry={() => historyQuery.refetch()} />
                )
              ) : (
                <PriceHistoryChart points={historyQuery.data?.points ?? []} />
              )}
              {comparisonQuery.isLoading ? (
                <PanelSkeleton />
              ) : comparisonQuery.isError ? (
                isAuthError(comparisonQuery.error) ? (
                  <SignInPanel />
                ) : (
                  <ErrorPanel
                    message={friendlyError(t, comparisonQuery.error)}
                    onRetry={() => comparisonQuery.refetch()}
                  />
                )
              ) : (
                <MarketComparison rows={comparisonQuery.data?.rows ?? []} />
              )}
            </div>
            <div className="space-y-6">
              <div className="rounded-xl border border-border bg-card p-4">
                <h3 className="text-sm font-semibold text-foreground">{t("markets.selectionSummary")}</h3>
                <div className="mt-3 space-y-3">
                  {[
                    {
                      key: "markets.reportedMarkets",
                      value: String(new Set((comparisonQuery.data?.rows ?? []).map((r) => r.market)).size),
                    },
                    {
                      key: "markets.observationsInTable",
                      value: String(latestQuery.data?.items.length ?? 0),
                    },
                    {
                      key: "markets.trendPoints",
                      value: String(historyQuery.data?.stats.point_count ?? 0),
                    },
                    {
                      key: "markets.latestObservation",
                      value: latestQuery.data?.freshness.latest_observation_date ?? "--",
                    },
                  ].map(({ key, value }) => (
                    <div key={key} className="flex items-center justify-between border-b border-border/50 pb-2 last:border-0">
                      <span className="text-xs text-muted-foreground">{t(key)}</span>
                      <span className="text-sm font-semibold text-foreground">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
              {latestQuery.data && (
                <div className="rounded-xl border border-border bg-card p-4">
                  <SourceAttribution provenance={latestQuery.data.provenance} />
                </div>
              )}
              <div className="rounded-xl border border-border bg-card p-4">
                <h3 className="text-sm font-semibold text-foreground">{t("markets.comingLater")}</h3>
                <p className="mt-1 text-xs text-muted-foreground">
                  {t("markets.comingLaterBody")}
                </p>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </DashboardLayout>
  );
}
