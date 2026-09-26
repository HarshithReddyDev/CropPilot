"""RainfallProvider: Open-Meteo ERA5 archive (past) + forecast API
(present/future) daily precipitation. All values are labelled
reanalysis/forecast estimate — never station-observed IMD rainfall
(IMD's web endpoints are unreachable from here; documented in
docs/map-data-sources.md).

Aggregates: today, last 7 days, current calendar month, monsoon season
(Jun–Sep, India), with nulls (never zero-filled) for missing days.
"""

from __future__ import annotations

from datetime import date, timedelta

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
# NOTE: archive-api subdomains are unreachable from some networks; the
# forecast endpoint serves past_days (ERA5) too, so rainfall uses ONE
# endpoint that is already proven for the weather service.
SOURCE = "open-meteo"
TIMEOUT_S = 20.0
PAST_DAYS = 92


async def _daily(lat: float, lng: float, start: str, end: str) -> dict[str, float | None]:
    import httpx

    params = {
        "latitude": lat, "longitude": lng,
        "daily": "precipitation_sum", "timezone": "auto",
    }
    # Past window (ERA5) + forecast window in one proven endpoint.
    past_days = max(0, (date.today() - date.fromisoformat(start)).days)
    future_days = max(1, (date.fromisoformat(end) - date.today()).days + 1)
    out: dict[str, float | None] = {}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            if past_days > 0:
                resp = await client.get(FORECAST_URL, params={
                    **params, "past_days": min(past_days, 92), "forecast_days": 1})
                out.update(_parse(resp))
            if future_days > 1 or past_days <= 0:
                resp = await client.get(FORECAST_URL, params={
                    **params, "past_days": 0, "forecast_days": min(future_days, 16)})
                out.update(_parse(resp))
    except Exception:
        pass
    # Clip to the requested window (past_days rounds to full availability).
    return {d: v for d, v in out.items() if start <= d <= end}


def _parse(resp) -> dict[str, float | None]:
    try:
        if resp.status_code != 200:
            return {}
        daily = (resp.json().get("daily") or {})
        times = daily.get("time") or []
        vals = daily.get("precipitation_sum") or []
        return {t: (float(v) if v is not None else None)
                for t, v in zip(times, vals)}
    except Exception:
        return {}


def _season_bounds(today: date) -> tuple[date, date, str]:
    """India southwest-monsoon season window containing `today`."""
    y = today.year
    start = date(y, 6, 1)
    end = date(y, 9, 30)
    if today < start:
        start, end = date(y - 1, 6, 1), date(y - 1, 9, 30)
    label = f"Jun–Sep {start.year}"
    return start, min(end, today), label


async def get_rainfall(lat: float, lng: float, timeout_s: float = 30.0) -> dict:
    """Rainfall context. Never raises: failures yield status unavailable."""
    import asyncio

    if not (-90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0):
        return {"status": "unavailable", "data": None, "source": SOURCE,
                "reason": "invalid-coordinates"}
    today = date.today()
    arch_start = (today - timedelta(days=60)).isoformat()
    try:
        async with asyncio.timeout(timeout_s):
            past = await _daily(lat, lng, arch_start, (today - timedelta(days=1)).isoformat())
            future = await _daily(lat, lng, today.isoformat(),
                                  (today + timedelta(days=7)).isoformat())
            obs: dict[str, float | None] = {**past, **future}
    except Exception:
        return {"status": "unavailable", "data": None, "source": SOURCE,
                "reason": "provider-timeout"}
    if not obs:
        return {"status": "unavailable", "data": None, "source": SOURCE,
                "reason": "no-data"}

    def total(days: list[str]) -> float | None:
        vals = [obs[d] for d in days if d in obs and obs[d] is not None]
        missing = [d for d in days if d not in obs or obs[d] is None]
        if not vals:
            return None
        # Honest gaps: a partial window is reported with its coverage.
        return round(sum(vals), 1) if not missing else round(sum(vals), 1)

    def window(n: int) -> list[str]:
        return [(today - timedelta(days=i)).isoformat() for i in range(n - 1, -1, -1)]

    today_v = obs.get(today.isoformat())
    week_days = window(7)
    month_days = [(today.replace(day=1) + timedelta(days=i)).isoformat()
                  for i in range((today - today.replace(day=1)).days + 1)]
    s_start, s_end, s_label = _season_bounds(today)
    season_days = []
    d = s_start
    while d <= s_end:
        season_days.append(d.isoformat())
        d += timedelta(days=1)

    def coverage(days: list[str]) -> str:
        have = sum(1 for x in days if x in obs and obs[x] is not None)
        return f"{have}/{len(days)} days"

    def covered_n(days: list[str]) -> int:
        return sum(1 for x in days if x in obs and obs[x] is not None)

    return {
        "status": "available",
        "data": {
            "today_mm": today_v,
            "last_7d_mm": total(week_days),
            "last_7d_coverage": coverage(week_days),
            "month_mm": total(month_days),
            "month_coverage": coverage(month_days),
            "season_mm": total(season_days),
            "season_label": s_label,
            "season_coverage": coverage(season_days),
            "season_days_total": len(season_days),
            "season_days_covered": covered_n(season_days),
        },
        "source": "Open-Meteo",
        "source_detail": "ERA5 reanalysis archive + forecast model",
        "mode": "modelled",
        "mode_note": ("Reanalysis/forecast estimate, not station-observed "
                      "IMD rainfall. Missing days are gaps, never zero-filled."),
        "observed_at": today.isoformat(),
    }
