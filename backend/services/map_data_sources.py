"""Map data-source registry: every external/internal source the map
actually uses. Sources that were probed but are NOT integrated
(CGWB/CWC/IMD/DES-OGD) are listed with enabled=false and the reason —
transparency in both directions."""

from __future__ import annotations


def source_registry() -> list[dict]:
    return [
        {"source_id": "agmarknet", "name": "AGMARKNET mandi data",
         "provider": "AGMARKNET via CropPilot Market Intelligence",
         "type": "market", "license": "Government open data (via CropPilot ingestion)",
         "coverage": "India (mandi network)", "granularity": "market/day",
         "refresh_frequency": "daily ingestion", "enabled": True,
         "notes": "Latest reported prices; never labelled live."},
        {"source_id": "open-meteo", "name": "Open-Meteo weather + rainfall",
         "provider": "Open-Meteo (ERA5 reanalysis + forecast models)",
         "type": "weather", "license": "CC-BY 4.0",
         "coverage": "global grid", "granularity": "point/hourly-daily",
         "refresh_frequency": "on demand (3 h weather staleness)",
         "enabled": True,
         "notes": "Rainfall is reanalysis/forecast estimate, not IMD station data."},
        {"source_id": "soilgrids", "name": "SoilGrids v2.0 (WCS)",
         "provider": "ISRIC — World Soil Information",
         "type": "soil", "license": "CC-BY 4.0",
         "coverage": "global, 250 m grid", "granularity": "250 m cell",
         "refresh_frequency": "static release (30-day local cache)",
         "enabled": True,
         "notes": "Modelled estimates via documented WCS GetCoverage (REST API unreliable)."},
        {"source_id": "nominatim", "name": "Nominatim geocoding",
         "provider": "OpenStreetMap contributors",
         "type": "geocoder", "license": "ODbL (usage policy respected)",
         "coverage": "global", "granularity": "place",
         "refresh_frequency": "live with 24 h cache", "enabled": True,
         "notes": "Server-side only; throttled, cached, India-biased."},
        {"source_id": "carto", "name": "CARTO basemaps",
         "provider": "CARTO + OpenStreetMap contributors",
         "type": "tiles", "license": "Documented keyless styles, attributed",
         "coverage": "global", "granularity": "vector tiles",
         "refresh_frequency": "provider-side", "enabled": True,
         "notes": "positron (light) / dark-matter (dark)."},
        {"source_id": "croppilot-taxonomy", "name": "CropPilot disease taxonomy + knowledge",
         "provider": "CropPilot (verified registry + curated IPM guidance)",
         "type": "disease-context", "license": "CropPilot internal",
         "coverage": "105 taxonomy rows", "granularity": "crop/disease",
         "refresh_frequency": "release-based", "enabled": True,
         "notes": "Crop-associated risks only; no prevalence or outbreak data."},
        {"source_id": "imd", "name": "IMD rainfall",
         "provider": "India Meteorological Department",
         "type": "rainfall", "license": "Government open data",
         "coverage": "India districts", "granularity": "district/day",
         "refresh_frequency": "unknown", "enabled": False,
         "notes": "Probed 2026-09-26: mausam.imd.gov.in and hydroimdie unreachable; "
                  "no verified machine-readable endpoint. Open-Meteo used instead."},
        {"source_id": "cgwb", "name": "CGWB groundwater",
         "provider": "Central Ground Water Board",
         "type": "groundwater", "license": "Government open data",
         "coverage": "India monitoring wells", "granularity": "monitoring well",
         "refresh_frequency": "quarterly observations", "enabled": False,
         "notes": "Probed 2026-09-26: no machine-readable WIMS API accessible; "
                  "observations published as reports. UI shows unavailable."},
        {"source_id": "cwc", "name": "CWC reservoir storage",
         "provider": "Central Water Commission",
         "type": "reservoir", "license": "Government open data",
         "coverage": "India reservoirs", "granularity": "reservoir",
         "refresh_frequency": "weekly bulletins", "enabled": False,
         "notes": "Probed 2026-09-26: bulletin pages unreachable/empty from here; "
                  "no verified machine endpoint. UI shows unavailable."},
        {"source_id": "des-ogd", "name": "DES district crop statistics",
         "provider": "Directorate of Economics & Statistics via data.gov.in",
         "type": "crops", "license": "Government open data (API key required)",
         "coverage": "India districts", "granularity": "district/season/year",
         "refresh_frequency": "annual", "enabled": False,
         "notes": "DATA_GOV_API_KEY not configured; AGMARKNET mandi trade mix "
                  "used instead (labelled market-observed)."},
    ]
