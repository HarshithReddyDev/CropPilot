# CropPilot demo checklist

## Prerequisites

- Docker Desktop / Docker Engine with Compose.
- Node.js compatible with the pinned frontend package and npm.
- Python environment or Docker image for backend tests/commands.
- No hosted AI key is required for core map, market and disease-uncertainty
  flows. Local assistant answers require the configured Ollama model; hosted
  assistant providers are optional.
- Copy `backend/.env.example` to `backend/.env` and set only credentials
  needed for the integrations you intend to demonstrate. Never commit `.env`.

## Start

```powershell
docker compose up -d --build
cd frontend
npm ci
npm run dev
```

Open `http://127.0.0.1:3000`. API: `http://127.0.0.1:8000`.
PostgreSQL is exposed on host port 5434; Grafana on 3001. The frontend is
run separately from Compose.

## Demo path

1. **Home / Dashboard:** explain CropPilot's farmer-facing workflow; do not
   present any explicitly marked sample/demo data as a real observation.
2. **Agricultural Map:** search/select Nalgonda, Telangana. Explain which
   context is available (weather, market trade, partial SoilGrids) and which
   is unavailable (CGWB/CWC/IMD/OGD in this deployment). Describe SoilGrids as
   modelled, rainfall as Open-Meteo reanalysis/forecast, and crops as mandi
   trade mix—not surveyed area.
3. **Market Intelligence:** select a location/commodity and show an actual
   latest reported AGMARKNET record with arrival date and source. Never call
   this "live price".
4. **Disease Detection:** use a real crop image only if available. Show image
   quality, model evidence and uncertainty. Do not infer crop from a model
   class or claim field accuracy.
5. **AI Assistant:** ask about selected map context or markets. Confirm
   citations/tool output are available; hosted providers may be unconfigured.
6. **Schemes / Weather / Analytics:** demonstrate only retrieved or sourced
   values; point out empty/unavailable states honestly.
7. **Language:** switch among shipped catalogs (English, Telugu, Hindi,
   Tamil, Bengali, Marathi, Gujarati, Nepali, Punjabi, Sanskrit, Urdu).
   UI translation coverage is currently 11 of 23 registered locales. Voice
   support is a separate, narrower capability matrix.

## Verification commands

```powershell
cd backend
python -m pytest tests/test_map.py tests/test_disease.py -q -o addopts=""
python -m services.disease validate
python -m services.disease healthcheck
cd ..\frontend
npm run i18n:validate
npm run i18n:audit
npm run typecheck
npx playwright test e2e/map.spec.ts e2e/disease.spec.ts
npm run build
```

## Shutdown

Stop the frontend dev process, then run `docker compose down` from the repo
root. Persistent database/model volumes are retained; remove them only if
you intentionally want to delete local state.

## Known demo limitations

- UI catalog coverage: 11/23; missing locale catalogs fall back to English.
- Map soil/WCS responses are partial; values are modelled estimates, not lab
  tests. Open-Meteo rainfall is not IMD station rainfall.
- Groundwater/reservoir/official district crop-statistics sections are
  unavailable until machine-readable sources are configured.
- Disease coverage is deliberately limited; there is no verified field/India
  validation or calibrated probability.
- A local demo account / bypass is development-only; never enable it in
  production.
