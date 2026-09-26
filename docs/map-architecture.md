# CropPilot Map Architecture

Route: `/maps` (upgraded in place; no duplicate routes).

## Frontend

- `app/maps/page.tsx` — search, selection, panel/bottom-sheet, layer toggle,
  URL state (`?lat=&lng=&zoom=`), geolocation, assistant handoff.
- `components/maps/croppilot-map.tsx` — MapLibre GL base map + native
  clustered GeoJSON market markers + branded selected-location div marker.
  Client-only (`next/dynamic`, `ssr: false`). No Leaflet, no deck.gl in the
  new path (deck.gl remains installed for other uses).
- `components/maps/map-search.tsx` — 300 ms debounced backend search,
  keyboard (ArrowUp/Down/Enter/Escape), ARIA combobox/listbox.
- `components/maps/location-panel.tsx` — location header, weather, nearby
  markets, market detail card, CropPilot action links. Each source loads and
  fails independently; sections render only for real data.
- `services/map.ts` — strict typed client (`apiFetch`, authed). No `any`.
- `hooks/use-map.ts` — React Query; coordinate-bucketed keys (`coordBucket`,
  ~1 km grid), stale times 10–60 min, `retry: 1`, auth-gated like markets.
- Removed: `map-view.tsx` (mock farms/markets/disease/weather),
  `map-container.tsx` (dead Mapbox-token gate), `map-controls.tsx`,
  `map-legend.tsx`, `disease-heatmap.tsx`, `market-overlay.tsx`,
  `weather-overlay.tsx`, `farm-boundary-layer.tsx`, `h3-hex-layer.tsx`.

## Backend (`/api/v1/map/*`, auth via existing dependency)

- `GET /map/search?q=` (2–100 chars) — local AGMARKNET geo catalog
  (states/districts/markets) blended with server-side Nominatim
  (India-biased). Every result carries `source`.
- `GET /map/reverse?lat=&lng=` — Nominatim reverse; never fails hard
  (nulls on provider error). Coordinate ranges validated (422 otherwise).
- `GET /map/markets?lat=&lng=&radius_km=&state=&district=&commodity=&limit=`
  — catalog candidates → on-demand coordinate resolution (≤5/call,
  persisted with provenance) → haversine sort → latest reported price per
  market from `market_prices`. Bounded (limit ≤ 50). Markets without
  coordinates are counted in `unmapped_count`, never placed.
- `GET /map/viewport-markets` — cached coordinates in bbox only (no live
  geocoding on pan/zoom; UI uses an explicit "Search this area" button).
- `GET /map/weather?lat=&lng=` — H3 res-7 cell → latest stored record;
  refreshes from Open-Meteo when missing/stale (>3 h) via the existing
  weather service; returns the real `recorded_at` (never "live").
- `services/map_geocoder.py` — Nominatim adapter: 1.1 s throttle, UA,
  10 s timeouts, in-memory TTL cache, market-name normalization
  (suffix/parenthesis stripping, no district-centroid fallback).
- `services/map_service.py` — orchestration, haversine, district-variant
  matching ("Nalgonda mandal" → catalog "Nalgonda").
- Migration `0010_geo_market_coordinates` (reversible): nullable
  `latitude/longitude/coordinate_source/coordinates_updated_at` on
  `geo_markets`. Plain floats (not PostGIS Geography) so the sqlite test
  suite keeps working; distance math is Python haversine over bounded sets.

## Viewport behavior

Selection commits on click only (rounded to 4 dp). Viewport queries fire
only via "Search this area". Nearby queries fire on selection change.
Weather fires on selection change. Nothing fires on zoom/pan.

## Agricultural intelligence (aggregate)

`GET /api/v1/map/agricultural-context?lat=&lng=&district=&state=` fans
out server-side over independent providers with per-provider timeouts
(75 s total bound): reverse, weather, rainfall, soil, crops,
suitability (rule engine, in-process), water, disease context. Each
section carries `{status, data, source, mode}`; failures degrade to
`{status: unavailable}` without failing the response. The browser makes
ONE request (plus the separate markets query). Caches: `soil_cache`
(30 d per ~100 m cell), `crop_context_cache` (7 d per district),
weather records (3 h staleness), in-memory geocoder TTL.
`GET /api/v1/map/data-sources` exposes the source registry live.

## URL state

`?lat=&lng=&zoom=` written on selection (replace, no scroll); restored on
load after range validation. No private data encoded.

## Privacy

No auto-geolocation (explicit button only); permission/timeout/unsupported
states mapped to honest copy. Precise coordinates are never logged
(request logs carry rounded buckets at most) and never persisted, except
market coordinates resolved from OSM (public places, provenance stored).

## Future layers

Layer control currently exposes only `markets` (genuine source). Provider
seams exist (`NominatimGeocoder`, `location_weather`, market query fns).
Soil, crop recommendations, and disease hotspots stay OFF — no data source
exists; the panel omits those sections rather than faking them.

## Performance

Bounded result sets (≤50 nearby, ≤200 viewport), debounced search with
cancellation via React Query, coordinate-bucketed caching, native maplibre
clustering (no per-market React components), theme-driven tile styles.
