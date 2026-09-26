"""Disease and farm-economics tools for the assistant.

Disease answers come from the farmer's own detection logs (never a
hardcoded disease dictionary). Profit math is pure arithmetic.
"""

from __future__ import annotations

from uuid import UUID

from db.session import async_session_factory
from services.disease_logs import DiseaseService

_disease = DiseaseService()


async def disease_log_summary(log_id: str) -> dict:
    """Summarize one vision detection log: crop, detections, confidence."""
    try:
        log_uuid = UUID(str(log_id))
    except (ValueError, TypeError):
        return {"ok": False, "error": f"invalid disease log id {log_id!r}"}
    async with async_session_factory() as db:
        try:
            log = await _disease.get_disease_log(db, log_uuid)
        except Exception as e:
            return {"ok": False, "error": f"disease log lookup failed: {e}"}
    if log is None:
        return {"ok": False, "error": f"no disease log {log_id}"}
    data = log.model_dump(mode="json") if hasattr(log, "model_dump") else dict(log)
    dets = data.get("detections") or []
    top = sorted(dets, key=lambda d: d.get("confidence", 0), reverse=True)[:3]
    return {
        "ok": True,
        "log_id": str(data.get("id") or log_id),
        "detections": [
            {
                "class_name": d.get("class_name"),
                "confidence": d.get("confidence"),
            }
            for d in top
        ],
        "created_at": data.get("created_at"),
    }


async def crop_profit(
    crop: str,
    area_hectares: float,
    expected_yield_per_hectare: float,
    market_price_per_quintal: float,
    cost_per_hectare: float,
) -> dict:
    """Expected profit arithmetic. All quantities must be non-negative."""
    vals = {
        "area_hectares": area_hectares,
        "expected_yield_per_hectare": expected_yield_per_hectare,
        "market_price_per_quintal": market_price_per_quintal,
        "cost_per_hectare": cost_per_hectare,
    }
    for k, v in vals.items():
        if v is None or float(v) < 0:
            return {"ok": False, "error": f"{k} must be non-negative"}
    total_yield = area_hectares * expected_yield_per_hectare
    revenue = total_yield * market_price_per_quintal
    cost = area_hectares * cost_per_hectare
    return {
        "ok": True,
        "crop": crop,
        "total_yield_quintals": round(total_yield, 2),
        "total_revenue_rs": round(revenue, 2),
        "total_cost_rs": round(cost, 2),
        "profit_rs": round(revenue - cost, 2),
    }
