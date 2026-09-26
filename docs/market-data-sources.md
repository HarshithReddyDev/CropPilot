# Market Data Sources Inventory

Machine-readable companion: `market_data_sources` table (seeded by migration
`0006_market_sources.py`). Status values: IMPLEMENTED, INVESTIGATE,
REQUIRES_ACCESS, LICENSED, NOT_PRACTICAL, DUPLICATE.

Only public APIs, public government endpoints, public downloadable datasets,
officially documented feeds, or sources permitted by their terms are
integrated. Nothing here bypasses login, authorization, CAPTCHA, rate limits,
or licensed feeds.

## AGMARKNET — IMPLEMENTED

- Organization: Directorate of Marketing and Inspection
- URL: https://api.agmarknet.gov.in/v1/ (public web backend of agmarknet.gov.in)
- Data types: mandi price (min/max/modal), arrivals, variety; grade on the
  market-report variant
- Geography: state/district/market via metadata IDs; 36 states/UTs, ~750
  districts, ~4170 markets observed live
- Commodities: ~605 in metadata
- History: price reports allowed from 2021-01-01 (per upstream range metadata)
- Update frequency: daily
- Public API: yes, no key; browser-like headers required (else nginx 403)
- Registration/API key: none
- License/redistribution: government public data; attribute AGMARKNET
- Duplicates: none; this is the core mandi provider
- Implementation: `services/agmarknet_client.py`, `services/market_providers.py`,
  tables `market_prices`, `market_ingestions`, `geo_states/districts/markets`.
  Arrivals from the daily-report variant persist as `market_prices.arrivals` /
  `arrival_unit` (quantity metadata only, never price); malformed arrivals
  store as NULL, never zero. Ingestion routing via `workers/tasks.py:
  ingest_source("AGMARKNET", ...)`.

## eNAM — REQUIRES_ACCESS

- Organization: Small Farmers Agribusiness Consortium (SFAC)
- URL: https://enam.gov.in/
- Data types: auctions, traded quantity, transaction/auction prices, APMC,
  trade activity, quality/assay fields (per official documentation)
- Public API: none found. Trade-data dashboard page is a JS app with no
  discoverable public endpoints. Integration is officially via SFAC
  empanelment/RFQ process.
- Duplicate risk: HIGH. Official docs describe AGMARKNET price information
  synchronized into eNAM. Never copy eNAM's AGMARKNET-derived values into the
  AGMARKNET table; eNAM-specific observations belong in `trade_observations`.
- Implementation status: architecture + `trade_observations` table ready; no
  client until access is granted. Do not reverse-engineer private endpoints.

## DCA_PMD — NOT_PRACTICAL

- Organization: Department of Consumer Affairs, Price Monitoring Division
- URL: https://fcainfoweb.nic.in/ (22 essential commodities, 555 centres)
- Data types: retail price, wholesale price, reporting centre, commodity, date
- Public API: none found. Verified live: `/api/dailyprices` returns 404;
  reports are ASP.NET WebForms pages (one report URL 302s). No stable
  machine interface exists.
- Implementation status: `consumer_prices` table ready; no client. Do not
  merge DCA wholesale values with AGMARKNET modal prices.

## DES_AGRI — NOT_PRACTICAL

- Organization: Directorate of Economics and Statistics
- URL: https://desagri.gov.in/ (also https://eands.da.gov.in/)
- Data types: wholesale prices, retail prices, farm harvest prices,
  international prices, statistical series (109 commodities / 237 markets /
  905 quotations cited for the WPI-related stream)
- Public API: none found. Monthly HTML dashboard tables and publications only.
- Implementation status: `agri_price_series` table ready; no client.

## STATE_APMC — INVESTIGATE

- Organization: various state authorities
- Data types: state-specific mandi data where published
- Status: provider registry/configuration model exists (`STATE_APMC` source
  code). Build a per-state inventory (portal, URL, API/download availability,
  access type, update frequency, AGMARKNET duplication) before writing any
  adapter. Do not build 36 adapters blindly.

## TRADESTAT — NOT_PRACTICAL

- Organization: Ministry of Commerce (DGCIS data)
- URL: https://tradestat.commerce.gov.in/ (monthly data Jan 2018–Jul 2026 observed)
- Data types: imports/exports by HS code (2/4/6/8 digit), country, region,
  month, value, quantity
- Public API: none found. Interactive form-driven query pages only.
- Implementation status: `trade_stats` table ready (value is never a price);
  no client.

## NCDEX — LICENSED

- Organization: National Commodity and Derivatives Exchange
- URL: https://www.ncdex.com/
- Data types: instrument, contract, OHLC, volume, open interest
- Access: daily market page is a JS app with no discoverable public API;
  detailed feeds are licensed products.
- Implementation status: `exchange_observations` table ready; no client.
  Do not circumvent access restrictions.

## MCX — LICENSED

- Organization: Multi Commodity Exchange
- URL: https://www.mcxindia.com/market-data/bhavcopy
- Data types: instrument, contract, OHLC, volume, open interest, spot
- Access: verified live 403 behind Akamai WAF with normal browser headers;
  bypassing would mean evading access controls, which is out of scope.
  Detailed data-feed products are subscription/licensed.
- Implementation status: `exchange_observations` table ready; no client.

## FCI — NOT_PRACTICAL

- Organization: Food Corporation of India
- URL: https://fci.gov.in/
- Data types: procurement information, stock information
- Public API: none found. HTML pages only; no stable machine interface exists.
- Implementation status: no table yet; log in source registry only.
  Never mix procurement/stock figures with mandi prices.

## CACP_MSP — NOT_PRACTICAL

- Organization: Commission for Agricultural Costs and Prices
- URL: https://cacp.dacnet.nic.in/
- Data types: MSP notifications, procurement prices, marketing seasons
- Public API: none found. Notifications published as documents; the CACP site
  was unreachable during discovery. No machine interface found.
- Implementation status: no table yet; log in source registry only.
  Never merge MSP values with observed market prices.
