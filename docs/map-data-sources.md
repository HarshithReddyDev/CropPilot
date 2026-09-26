# CropPilot Map Data Sources

Every source below is actually used. Names here match runtime behavior.
`GET /api/v1/map/data-sources` exposes the same registry live.

## Map tiles

- Light: `https://basemaps.cartocdn.com/gl/positron-gl-style/style.json`
- Dark: `https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json`
- Provider: CARTO basemaps (documented, keyless). Attribution rendered by
  MapLibre from the style document (© OpenStreetMap contributors © CARTO).
- Override (optional, no secrets): `NEXT_PUBLIC_MAP_TILE_URL`.
- No Google tile endpoints anywhere in the codebase.

## Geocoding / reverse geocoding

- Provider: OpenStreetMap Nominatim (`https://nominatim.openstreetmap.org`),
  server-side only, India-biased (`countrycodes=in`).
- No API key. Usage policy respected: ≥1.1 s between requests, proper
  User-Agent, 10 s timeouts, in-memory TTL cache, result limits.
- Local complement: CropPilot AGMARKNET geo catalog (`geo_states`,
  `geo_districts`, `geo_markets`) for state/district/market-name search.

## Market data

- AGMARKNET via CropPilot Market Intelligence (`market_prices`:
  state/district/market/commodity/variety/grade/arrival_date/modal_price).
- Map shows the **latest reported** observation per market (never "live").
- Market coordinates: `geo_markets.latitude/longitude`, populated only
  from OSM geocoding with `coordinate_source='nominatim/osm'` provenance.
  Coverage is partial by design; unmapped markets are counted, not placed.
  No coordinates are fabricated. District-name variants are normalized
  ("Nalgonda mandal" matches catalog "Nalgonda").

## Weather

- Existing CropPilot weather service, Open-Meteo provider (CC-BY 4.0),
  H3-res-7 indexed storage. Map requests refresh when missing/stale (>3 h)
  and report the real `recorded_at` timestamp as freshness.

## Rainfall

- Open-Meteo forecast endpoint with `past_days` (ERA5 reanalysis) +
  7-day forecast. Aggregates: today / last 7 days / calendar month /
  Jun–Sep monsoon season, each with day-coverage (gaps shown, never
  zero-filled). Labelled **modelled** (reanalysis/forecast estimate).
- IMD probed 2026-09-26: `mausam.imd.gov.in` and `hydroimdie` unreachable
  from here; no verified machine-readable endpoint. If IMD access appears,
  only the fetch function in `services/agri_rain.py` needs to change.

## Soil

- SoilGrids v2.0 (2020 release), CC-BY 4.0, via documented **WCS 2.0.1
  GetCoverage** (`https://maps.isric.org/mapserv`, per-property
  `0-5cm_mean` coverages over a ±0.02° box, parsed with tifffile).
  The REST API was verified unreachable (connection failures); WCS works
  but is slow/flaky, so properties fetch with short timeouts, mild
  parallelism, and a 30-day per-cell DB cache (`soil_cache`).
- Properties: pH, organic carbon, sand/silt/clay %, CEC, nitrogen.
  Texture names come from the USDA triangle only — never invented soil
  orders. Labelled **modelled estimate**, 250 m resolution, with license.
- Uncertainty layers exist but their scaling is not documented well
  enough to display numbers honestly — not surfaced.

## Crops

- AGMARKNET mandi arrivals per district (trailing 12 months, top 8 by
  arrival volume, 7-day `crop_context_cache`). Labelled **market-observed
  trade mix**, explicitly "not a farm survey of what is grown".
  `DES/OGD` district statistics need `DATA_GOV_API_KEY` (not configured).

## Suitability

- CropPilot rule engine (`services/agri_crops.py`): explicit requirement
  thresholds (rainfall, temperature, texture set, pH range, organic-carbon
  floor) per crop; each factor suitable/marginal/unsuitable, band = worst
  factor. **No weights, no numeric scores.** Water-demanding crops cap at
  Moderate (irrigation unknown). Labelled **derived estimate** with a
  yield/profitability disclaimer. Only district-traded crops are assessed.

## Groundwater / reservoirs

- Providers (`services/agri_water.py`) and UI exist, but CGWB WIMS and CWC
  bulletin endpoints are not machine-accessible from here (probed
  2026-09-26: India-WRIS unreachable, CWC pages empty/unreachable, CGWB
  site has no JSON API). Both sections honestly report unavailable with
  the reason. Enabling them later = implementing the two fetch functions.

## Disease context

- CropPilot disease taxonomy (105 rows) + knowledge entries, grouped by
  the area's traded crops. **Crop-associated risks, never outbreaks** —
  no prevalence, no probabilities, no hotspot layer.

## Explicitly NOT present

Soil lab tests, IMD station rainfall, live groundwater levels, reservoir
storage numbers, crop-yield statistics, disease prevalence: no authoritative
accessible source exists, so no such value is shown anywhere on the map.
The old mock farm polygons, random disease points, hardcoded market
prices, and fake weather stations were deleted.
