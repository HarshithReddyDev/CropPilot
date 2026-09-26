"use client";

import Link from "next/link";
import { useState } from "react";
import { formatNumber, useTranslation } from "@/lib/i18n";
import { Badge } from "@/components/ui/badge";
import type {
  AgriContext,
  MapMarket,
  MapMarketsResponse,
  MapReverseResult,
  MapWeather,
} from "@/services/map";

interface LocationPanelProps {
  lat: number;
  lng: number;
  reverse: MapReverseResult | null;
  reverseLoading: boolean;
  reverseError: boolean;
  weather: MapWeather | null;
  weatherLoading: boolean;
  weatherError: boolean;
  agri: AgriContext | null;
  agriLoading: boolean;
  agriError: boolean;
  markets: MapMarketsResponse | null;
  marketsLoading: boolean;
  marketsError: boolean;
  commodity: string;
  onCommodity: (c: string) => void;
  onSearchArea: () => void;
  searchAreaLoading: boolean;
  selectedMarket: MapMarket | null;
  onMarketSelect: (m: MapMarket | null) => void;
  onAskAssistant: () => void;
}

function Section({
  title,
  action,
  children,
}: {
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
        {action}
      </div>
      {children}
    </section>
  );
}

function Collapsible({
  title,
  badge,
  defaultOpen = false,
  children,
}: {
  title: string;
  badge?: string | null;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="overflow-hidden rounded-xl border border-border/50">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-2 bg-card px-4 py-3 text-left"
      >
        <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
          {title}
          {badge && (
            <Badge variant="outline" className="text-[10px] font-normal">
              {badge}
            </Badge>
          )}
        </span>
        <svg
          className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open && <div className="space-y-3 border-t border-border/50 p-4">{children}</div>}
    </section>
  );
}

function StateLine({ label, value }: { label: string; value: string }) {
  return (
    <p className="rounded-lg bg-muted/50 px-4 py-3 text-sm text-muted-foreground" role="status">
      <span className="font-medium text-foreground">{label} </span>
      {value}
    </p>
  );
}

function KV({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-2 rounded-lg bg-muted/50 px-3 py-2 text-xs">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="text-end font-medium text-foreground">{v}</dd>
    </div>
  );
}

function fmtCoords(lat: number, lng: number): string {
  const la = `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? "N" : "S"}`;
  const lo = `${Math.abs(lng).toFixed(4)}° ${lng >= 0 ? "E" : "W"}`;
  return `${la}, ${lo}`;
}

function fmtNum(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return "—";
  return v.toFixed(digits);
}

function marketHref(m: MapMarket, commodity?: string | null): string {
  const p = new URLSearchParams();
  if (m.state) p.set("state", m.state);
  if (m.district) p.set("district", m.district);
  p.set("market", m.name);
  const c = commodity || m.latest?.commodity;
  if (c) p.set("commodity", c);
  return `/markets?${p.toString()}`;
}

/** Location intelligence panel. Sections render only for real data; each
 *  provider degrades independently. Modelled/estimated/derived values are
 *  labelled as such — never presented as observations. */
export function LocationPanel(props: LocationPanelProps) {
  const { t, locale } = useTranslation();
  const {
    lat, lng, reverse, reverseLoading, reverseError,
    weather, weatherLoading, weatherError,
    agri, agriLoading, agriError,
    markets, marketsLoading, marketsError,
    commodity, onCommodity, onSearchArea, searchAreaLoading,
    selectedMarket, onMarketSelect, onAskAssistant,
  } = props;

  const placeTitle = reverse?.locality ?? reverse?.district ?? null;
  const placeSub = [reverse?.district, reverse?.state, reverse?.country]
    .filter(Boolean)
    .join(", ");

  const snap = agri?.snapshot ?? null;
  const soil = agri?.soil ?? null;
  const soilD = soil?.data ?? null;
  const rain = agri?.rainfall ?? null;
  const rainD = rain?.data ?? null;
  const crops = agri?.crops ?? null;
  const cropsD = crops?.data ?? null;
  const suit = agri?.suitability ?? null;
  const suitD = suit?.data ?? null;
  const water = agri?.water ?? null;
  const disease = agri?.disease_context ?? null;
  const diseaseD = disease?.data ?? null;
  const wxTemp = weather?.temperature_c;
  const wxHum = weather?.humidity_pct;
  const wxRain = weather?.rain_mm;
  const wxOk = !weatherError && wxTemp != null;

  const commodities = Array.from(
    new Set(
      (markets?.markets ?? []).map((m) => m.latest?.commodity).filter(Boolean) as string[]
    )
  ).sort();

  const bandStyle = (band: string) =>
    band === "High"
      ? "text-emerald-600 bg-emerald-500/10"
      : band === "Moderate"
        ? "text-amber-600 bg-amber-500/10"
        : "text-slate-500 bg-slate-500/10";

  return (
    <div className="space-y-6" aria-live="polite">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          {t("maps.location")}
        </p>
        {reverseLoading ? (
          <div className="mt-1 h-6 w-40 animate-pulse rounded bg-muted" />
        ) : (
          <>
            <h2 className="mt-1 text-lg font-bold text-foreground">
              {placeTitle ?? fmtCoords(lat, lng)}
            </h2>
            <p className="text-sm text-muted-foreground">
              {placeSub || fmtCoords(lat, lng)}
            </p>
            {reverseError && (
              <p className="mt-1 text-xs text-muted-foreground">{t("maps.placeUnavailable")}</p>
            )}
          </>
        )}
      </div>

      {snap && (snap.common_crops?.length || snap.soil?.texture || snap.season_rain_mm != null) ? (
        <div className="space-y-2 rounded-xl border border-border/50 bg-card p-4">
          <p className="text-sm font-semibold text-foreground">{t("maps.agriSnapshot")}</p>
          {snap.common_crops && snap.common_crops.length > 0 && (
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{t("maps.commonCrops")}: </span>
              {snap.common_crops.join(" · ")}
            </p>
          )}
          {(snap.soil?.texture || snap.soil?.ph != null) && (
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{t("maps.soil")}: </span>
              {[snap.soil.texture, snap.soil.ph != null ? `pH ${snap.soil.ph}` : null]
                .filter(Boolean)
                .join(" · ")}
            </p>
          )}
          {snap.season_rain_mm != null && (
            <p className="text-xs text-muted-foreground">
              <span className="font-medium text-foreground">{t("maps.rainfall")}: </span>
              {t("maps.seasonRain", {
                mm: Math.round(snap.season_rain_mm),
                season: snap.season_label ?? "",
              })}
            </p>
          )}
        </div>
      ) : null}

      <Section title={t("maps.weather")}>
        {weatherLoading ? (
          <div className="h-20 animate-pulse rounded-xl bg-muted/50" />
        ) : weatherError || !wxOk ? (
          <StateLine label={t("maps.weather")} value={t("maps.weatherUnavailable")} />
        ) : (
          <div className="rounded-xl border border-border/50 bg-card p-4">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-foreground">{Math.round(wxTemp)}°C</span>
              <span className="text-xs text-muted-foreground">{t("maps.forecastLabel")}</span>
            </div>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div className="flex justify-between gap-2 rounded-lg bg-muted/50 px-3 py-2">
                <dt className="text-muted-foreground">{t("maps.humidity")}</dt>
                <dd className="font-medium text-foreground">
                  {wxHum ?? "—"}
                  {wxHum !== null && wxHum !== undefined ? "%" : ""}
                </dd>
              </div>
              <div className="flex justify-between gap-2 rounded-lg bg-muted/50 px-3 py-2">
                <dt className="text-muted-foreground">{t("maps.rain")}</dt>
                <dd className="font-medium text-foreground">
                  {wxRain ?? "—"}
                  {wxRain !== null && wxRain !== undefined ? " mm" : ""}
                </dd>
              </div>
            </dl>
            <p className="mt-2 text-[11px] text-muted-foreground">
              {t("maps.sourceOpenMeteo")}
            </p>
          </div>
        )}
      </Section>

      <Collapsible title={t("maps.soil")} badge={soilD ? t("maps.modelledBadge") : null} defaultOpen={false}>
        {agriLoading ? (
          <div className="h-24 animate-pulse rounded-xl bg-muted/50" />
        ) : !soilD ? (
          <StateLine label={t("maps.soil")} value={t("maps.soilUnavailable")} />
        ) : (
          <dl className="grid grid-cols-2 gap-2">
            {soilD.texture && <KV k={t("maps.texture")} v={soilD.texture} />}
            {soilD.ph != null && <KV k="pH" v={soilD.ph.toFixed(1)} />}
            {soilD.organic_carbon_pct != null && (
              <KV k={t("maps.organicCarbon")} v={`${soilD.organic_carbon_pct.toFixed(2)}%`} />
            )}
            {soilD.clay_pct != null && <KV k={t("maps.clay")} v={`${soilD.clay_pct.toFixed(0)}%`} />}
            {soilD.sand_pct != null && <KV k={t("maps.sand")} v={`${soilD.sand_pct.toFixed(0)}%`} />}
            {soilD.silt_pct != null && <KV k={t("maps.silt")} v={`${soilD.silt_pct.toFixed(0)}%`} />}
            {soilD.cec_cmolkg != null && <KV k="CEC" v={`${soilD.cec_cmolkg.toFixed(1)}`} />}
            {soilD.nitrogen_gkg != null && <KV k={t("maps.nitrogen")} v={`${soilD.nitrogen_gkg.toFixed(2)}`} />}
          </dl>
        )}
        {soil && (
          <p className="text-[11px] text-muted-foreground">
            {t("maps.sourceSoilGrids")} · {t("maps.resolutionM", { m: soil.resolution_m ?? 250 })}
            {soilD ? ` · ${t("maps.modelledEstimateNote")}` : ""}
          </p>
        )}
      </Collapsible>

      <Collapsible title={t("maps.rainfall")} defaultOpen={false}>
        {agriLoading ? (
          <div className="h-24 animate-pulse rounded-xl bg-muted/50" />
        ) : !rainD ? (
          <StateLine label={t("maps.rainfall")} value={t("maps.rainfallUnavailable")} />
        ) : (
          <dl className="grid grid-cols-2 gap-2">
            <KV k={t("maps.today")} v={rainD.today_mm != null ? `${fmtNum(rainD.today_mm)} mm` : "—"} />
            <KV k={t("maps.last7days")} v={rainD.last_7d_mm != null ? `${fmtNum(rainD.last_7d_mm)} mm` : "—"} />
            <KV k={t("maps.thisMonth")} v={rainD.month_mm != null ? `${fmtNum(rainD.month_mm)} mm` : "—"} />
            <KV
              k={rainD.season_label ?? t("maps.season")}
              v={rainD.season_mm != null ? `${fmtNum(rainD.season_mm, 0)} mm` : "—"}
            />
          </dl>
        )}
        {rain && rainD && (
          <p className="text-[11px] text-muted-foreground">
            {t("maps.sourceOpenMeteo")} · {t("maps.reanalysisNote")}
            {rainD.last_7d_coverage ? ` · ${rainD.last_7d_coverage}` : ""}
          </p>
        )}
      </Collapsible>

      <Collapsible title={t("maps.crops")} defaultOpen={false}>
        {agriLoading ? (
          <div className="h-24 animate-pulse rounded-xl bg-muted/50" />
        ) : !cropsD?.common?.length ? (
          <StateLine label={t("maps.crops")} value={t("maps.cropsUnavailable")} />
        ) : (
          <>
            <p className="text-xs text-muted-foreground">{t("maps.commonlyTraded")}</p>
            <div className="flex flex-wrap gap-2">
              {cropsD.common.map((c) => (
                <Badge key={c.commodity} variant="secondary" className="text-[11px]">
                  {c.commodity}
                </Badge>
              ))}
            </div>
            <p className="text-[11px] text-muted-foreground">
              {cropsD.interpretation} {t("maps.sourceAgmarknet")}
              {crops?.data_year ? ` · ${crops.data_year}` : ""}
            </p>
          </>
        )}
        {suitD?.estimates && suitD.estimates.length > 0 && (
          <div className="space-y-2 pt-1">
            <p className="text-xs font-medium text-foreground">{t("maps.suitabilityTitle")}</p>
            {suitD.estimates.map((e) => (
              <div key={e.crop} className="rounded-lg bg-muted/50 px-3 py-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-foreground">{e.crop}</span>
                  <Badge className={`border-0 text-[10px] ${bandStyle(e.suitability_band)}`}>
                    {e.suitability_band}
                  </Badge>
                </div>
                {e.limitations.length > 0 && (
                  <p className="mt-1 text-[11px] text-muted-foreground">{e.limitations.join("; ")}</p>
                )}
              </div>
            ))}
            <p className="text-[11px] text-muted-foreground">{suit?.data?.disclaimer}</p>
          </div>
        )}
      </Collapsible>

      <Collapsible title={t("maps.water")} defaultOpen={false}>
        <StateLine label={t("maps.water")} value={t("maps.waterUnavailable")} />
        <p className="text-[11px] text-muted-foreground">{t("maps.waterNote")}</p>
      </Collapsible>

      <Collapsible title={t("maps.diseaseContext")} defaultOpen={false}>
        {!diseaseD?.crop_risks?.length ? (
          <StateLine label={t("maps.diseaseContext")} value={t("maps.diseaseUnavailable")} />
        ) : (
          <>
            {diseaseD.crop_risks.map((r) => (
              <div key={r.crop} className="space-y-1">
                <p className="text-xs font-medium capitalize text-foreground">{r.crop}</p>
                <ul className="space-y-0.5">
                  {r.diseases.map((d) => (
                    <li key={d.disease_id} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-amber-500" aria-hidden="true" />
                      {d.display_name}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            <p className="text-[11px] text-muted-foreground">{diseaseD.interpretation}</p>
          </>
        )}
      </Collapsible>

      <Section
        title={t("maps.nearbyMarkets")}
        action={
          <div className="flex items-center gap-2">
            {commodities.length > 0 && (
              <select
                value={commodity}
                onChange={(e) => onCommodity(e.target.value)}
                aria-label={t("maps.commodityFilter")}
                className="max-w-[10rem] rounded-lg border border-border bg-background px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="">{t("maps.allCommodities")}</option>
                {commodities.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            )}
            <button
              type="button"
              onClick={onSearchArea}
              disabled={searchAreaLoading}
              className="rounded-lg border border-border px-2 py-1 text-xs font-medium text-foreground hover:bg-muted disabled:opacity-50"
            >
              {t("maps.searchArea")}
            </button>
          </div>
        }
      >
        {marketsLoading ? (
          <div className="h-24 animate-pulse rounded-xl bg-muted/50" />
        ) : marketsError ? (
          <StateLine label={t("maps.markets")} value={t("maps.marketsUnavailable")} />
        ) : !markets || markets.markets.length === 0 ? (
          <StateLine label={t("maps.markets")} value={t("maps.noMappedMarkets")} />
        ) : (
          <ul className="space-y-2">
            {markets.markets.map((m) => (
              <li key={`${m.state}|${m.district}|${m.name}`}>
                <button
                  type="button"
                  onClick={() => onMarketSelect(selectedMarket?.name === m.name ? null : m)}
                  aria-label={`${m.name}, ${m.district ?? ""}`}
                  className={`w-full rounded-xl border p-3 text-left transition-colors hover:bg-muted/50 ${
                    selectedMarket?.name === m.name
                      ? "border-primary bg-primary/5"
                      : "border-border/50 bg-card"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-semibold text-foreground">{m.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {[m.district, m.state].filter(Boolean).join(", ")}
                        {m.distance_km !== null && m.distance_km !== undefined
                          ? ` · ${m.distance_km} km`
                          : ""}
                      </p>
                    </div>
                  </div>
                  {m.latest?.modal_price !== null && m.latest?.modal_price !== undefined ? (
                    <p className="mt-1 text-sm text-foreground">
                      <span className="font-bold">
                        ₹{formatNumber(locale, m.latest.modal_price)}
                      </span>{" "}
                      <span className="text-xs text-muted-foreground">
                        / {t("maps.quintal")}
                        {m.latest.commodity ? ` · ${m.latest.commodity}` : ""}
                        {m.latest.variety ? ` (${m.latest.variety})` : ""}
                      </span>
                    </p>
                  ) : (
                    <p className="mt-1 text-xs text-muted-foreground">{t("maps.noReportedPrice")}</p>
                  )}
                  {m.latest?.arrival_date && (
                    <p className="mt-0.5 text-[11px] text-muted-foreground">
                      {t("maps.latestReported", { date: m.latest.arrival_date })} ·{" "}
                      {t("maps.sourceAgmarknet")}
                    </p>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
        {markets && markets.unmapped_count > 0 && (
          <p className="text-[11px] text-muted-foreground">
            {t("maps.unmappedNote", { count: markets.unmapped_count })}
          </p>
        )}
      </Section>

      {selectedMarket && (
        <div className="rounded-xl border border-primary/30 bg-primary/5 p-4">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-sm font-bold text-foreground">{selectedMarket.name}</p>
              <p className="text-xs text-muted-foreground">
                {[selectedMarket.district, selectedMarket.state].filter(Boolean).join(", ")}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onMarketSelect(null)}
              aria-label={t("maps.closeDetails")}
              className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground hover:bg-muted"
            >
              <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path d="M6 18 18 6M6 6l12 12" strokeLinecap="round" />
              </svg>
            </button>
          </div>
          {selectedMarket.latest?.modal_price !== null &&
          selectedMarket.latest?.modal_price !== undefined ? (
            <p className="mt-2 text-sm text-foreground">
              <span className="font-bold">
                ₹{formatNumber(locale, selectedMarket.latest.modal_price)}
              </span>{" "}
              <span className="text-xs text-muted-foreground">
                / {t("maps.quintal")}
                {selectedMarket.latest.commodity ? ` · ${selectedMarket.latest.commodity}` : ""}
                {selectedMarket.latest.variety ? ` (${selectedMarket.latest.variety})` : ""}
                {selectedMarket.latest.grade ? ` · ${selectedMarket.latest.grade}` : ""}
              </span>
            </p>
          ) : (
            <p className="mt-2 text-xs text-muted-foreground">{t("maps.noReportedPrice")}</p>
          )}
          {selectedMarket.latest?.arrival_date && (
            <p className="mt-0.5 text-[11px] text-muted-foreground">
              {t("maps.latestReported", { date: selectedMarket.latest.arrival_date })} ·{" "}
              {t("maps.sourceAgmarknet")}
            </p>
          )}
          <Link
            href={marketHref(selectedMarket, commodity || undefined)}
            className="mt-3 inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground"
          >
            {t("maps.viewMarketIntel")}
          </Link>
        </div>
      )}

      <Section title={t("maps.cropPilotActions")}>
        <div className="grid grid-cols-1 gap-2">
          <Link
            href="/markets"
            className="rounded-xl border border-border/50 bg-card px-4 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted/50"
          >
            {t("maps.openMarketIntel")}
          </Link>
          <Link
            href="/disease-detection"
            className="rounded-xl border border-border/50 bg-card px-4 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted/50"
          >
            {t("maps.analyzeDisease")}
          </Link>
          <button
            type="button"
            onClick={onAskAssistant}
            className="rounded-xl border border-border/50 bg-card px-4 py-3 text-left text-sm font-medium text-foreground transition-colors hover:bg-muted/50"
          >
            {t("maps.askAssistant")}
          </button>
        </div>
      </Section>

      <div className="flex flex-wrap gap-2">
        <Badge variant="outline" className="text-[10px]">
          {t("maps.legendSelected")}
        </Badge>
        <Badge variant="outline" className="text-[10px]">
          {t("maps.legendMarkets")}
        </Badge>
      </div>
    </div>
  );
}
