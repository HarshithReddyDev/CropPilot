# Known limitations

## Data coverage and freshness

- Markets use AGMARKNET **reported** prices with their recorded arrival
  dates. Geographic coordinates are geocoded and cached only when verified;
  unmapped markets are omitted rather than placed at district centroids.
- Weather uses Open-Meteo. Rainfall history is modelled reanalysis and
  forecast, not IMD station observations; missing days are surfaced as
  coverage gaps.
- SoilGrids WCS is slow/flaky and coverage is partial. Returned values are
  modelled 250 m soil-property estimates, not farm laboratory measurements;
  only non-null source values should be displayed.
- CGWB groundwater, CWC reservoir storage, IMD station rainfall and OGD/DES
  district crop-production statistics are unavailable in the current
  deployment. The map reports these sections unavailable rather than
  substituting invented values.
- Crop context currently uses recent AGMARKNET mandi arrivals as a proxy for
  market-traded commodities, not a government crop-area survey.
- Crop suitability bands are rule-based environmental estimates with no
  weighted score; irrigation access is unknown and water-demanding crops are
  capped accordingly. These are not yield/profit recommendations.

## Disease detection

- Only a small set of verified production model paths exists. The taxonomy
  contains more diseases than runnable models.
- No model is field-validated or India-validated. Model scores are not
  calibrated probabilities. PlantVillage labels do not establish the crop
  shown in an image; no crop classifier currently exists.
- Research-only/unlicensed models are gated. VLM fallback is optional and
  may be unconfigured.

## Languages and voice

- Canonical locale registry contains 23 Indian languages, but only 11 UI
  message catalogs currently exist: English, Telugu, Hindi, Tamil, Bengali,
  Marathi, Gujarati, Nepali, Punjabi, Sanskrit and Urdu. Other locales fall
  back to English and must not be described as fully translated.
- UI catalog coverage is separate from ASR/TTS/voice coverage. See
  `docs/assistant-voice.md` for the verified voice engines/language matrix.

## Deployment / scale

- Current Compose setup is a local development/single-host architecture; no
  multi-cloud deployment, autoscaling capacity, SLA, cost or throughput
  benchmark is claimed.
- A local frontend is started separately; Docker Compose provides backend,
  database, workers and observability services.
