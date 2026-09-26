"""WaterContextProvider + CropDiseaseContextProvider.

WATER: CGWB groundwater and CWC reservoir bulletins have no verified
machine-readable access from here (probed 2026-09-26: WIMS/WRI S APIs
unreachable, CWC bulletin pages empty/unreachable, mausam/IMD down).
The provider interface, registry entries, caching shapes, UI sections,
and map-layer slots all exist — but every field resolves to an explicit
unavailable state rather than a fabricated number. When an accessible
source appears, only the fetch functions below need to change.

DISEASE CONTEXT: fully implemented from CropPilot's own verified assets
(disease taxonomy + knowledge JSON). Crop-associated risks grouped by the
district's traded crops — never prevalence, outbreaks, or probabilities.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


# ------------------------------------------------------------------ water --

async def get_water_context(db: AsyncSession, lat: float, lng: float,
                            district: str | None, state: str | None) -> dict:
    """Groundwater + reservoirs. Currently unavailable everywhere; the
    shape below is the contract a future CGWB/CWC fetch will fill."""
    _ = (db, lat, lng, district, state)
    return {
        "status": "unavailable",
        "data": None,
        "reason": "no-accessible-source",
        "reason_note": ("No machine-readable CGWB groundwater or CWC reservoir "
                        "source is accessible. Periodic official observations are "
                        "published as reports/bulletins, not queryable data."),
        "groundwater": {"status": "unavailable", "data": None, "source": "CGWB",
                        "granularity": "monitoring well",
                        "mode": "observed",
                        "mode_note": "CGWB measures depth below ground level four times a year."},
        "reservoirs": {"status": "unavailable", "data": None, "source": "CWC",
                       "granularity": "point",
                       "mode": "observed",
                       "mode_note": "CWC publishes periodic storage bulletins."},
    }


# ------------------------------------------------------ disease context --

def get_disease_context(common_crops: list[str]) -> dict:
    """Crop-associated disease risks for crops traded in the area.

    Sources: CropPilot disease taxonomy (stable IDs, display names,
    Telangana/India priority flags) + knowledge entries where present.
    Labels say 'risks', never outbreaks; no percentages, no maps.
    """
    from services.disease import knowledge as knowledge_mod
    from services.disease import taxonomy as taxonomy_mod

    if not common_crops:
        return {"status": "unavailable", "data": None,
                "reason": "no-crop-context",
                "reason_note": "Disease risks need a crop list first."}
    crop_keys = {c.strip().lower().replace(" ", "_") for c in common_crops}
    # Map traded commodity names to taxonomy crop keys (paddy->rice etc.).
    aliases = {"paddy": "rice", "dhan": "rice", "mirchi": "chilli",
               "makka": "maize", "jowar": "sorghum", "bajra": "pearl_millet",
               "tur": "pigeon_pea", "chana": "chickpea", "urad": "black_gram",
               "moong": "green_gram", "groundnut": "groundnut", "til": "sesame"}
    wanted = {aliases.get(c, c) for c in crop_keys}
    risks: list[dict] = []
    for crop in sorted(wanted):
        rows = taxonomy_mod.diseases_for_crop(crop)
        if not rows:
            continue
        diseases = []
        for r in rows[:6]:
            did = str(r.get("id", ""))
            entry = {"disease_id": did,
                     "display_name": str(r.get("display_name", did)),
                     "priority": ("telangana-high" if r.get("telangana") == "high"
                                  else "india-high" if r.get("india") == "high" else None)}
            try:
                kn = knowledge_mod.get_entry(did)
            except Exception:
                kn = None
            entry["has_guidance"] = kn is not None
            diseases.append(entry)
        risks.append({"crop": crop, "diseases": diseases})
    if not risks:
        return {"status": "unavailable", "data": None,
                "reason": "no-taxonomy-match",
                "reason_note": "No taxonomy rows match the area's traded crops."}
    return {
        "status": "available",
        "data": {
            "crop_risks": risks,
            "interpretation": ("Crop-associated risks for crops traded in this area — "
                               "not confirmed local outbreaks. No prevalence data exists."),
        },
        "source": "CropPilot disease taxonomy + knowledge",
        "mode": "knowledge-derived",
    }
