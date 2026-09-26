"""Server-side client for AGMARKNET mandi prices via data.gov.in (OGD Platform).

Backend only. The API key must never reach the browser.
"""

from __future__ import annotations

import structlog
from httpx import AsyncClient, HTTPError, Response

from core.config import settings

logger = structlog.get_logger(__name__)

DEFAULT_RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"

# OGD caps page size; keep requests bounded.
MAX_PAGE_SIZE = 1000
# Safety bound so a runaway total cannot page forever.
MAX_PAGES = 100


class OgdConfigError(RuntimeError):
    """Raised when the OGD integration is not configured (e.g. missing key)."""


class OgdUpstreamError(RuntimeError):
    """Raised when the upstream OGD API fails or returns invalid data."""


def _filter_params(
    state: str | None,
    district: str | None,
    market: str | None,
    commodity: str | None,
    variety: str | None,
    grade: str | None,
) -> dict[str, str]:
    """Build OGD filter params. State uses the `.keyword` field per API contract."""
    params: dict[str, str] = {}
    if state:
        params["filters[state.keyword]"] = state
    if district:
        params["filters[district]"] = district
    if market:
        params["filters[market]"] = market
    if commodity:
        params["filters[commodity]"] = commodity
    if variety:
        params["filters[variety]"] = variety
    if grade:
        params["filters[grade]"] = grade
    return params


async def fetch_mandi_records(
    state: str | None = None,
    district: str | None = None,
    market: str | None = None,
    commodity: str | None = None,
    variety: str | None = None,
    grade: str | None = None,
    limit_total: int = 1000,
    api_key: str | None = None,
    resource_id: str | None = None,
    base_url: str | None = None,
    timeout: int | None = None,
    page_size: int | None = None,
) -> tuple[list[dict], bool]:
    """Fetch raw mandi records from OGD with pagination.

    Returns (records, truncated). Truncated is True when the source holds
    more records than the safety bound allowed us to fetch, so callers can
    audit a capped partial pull instead of reporting it as complete.
    No value coercion happens here; see `services.market_normalization`
    for parsing. Raises `OgdConfigError` when no API key is configured and
    `OgdUpstreamError` on HTTP/transport failures or invalid payloads.
    """
    key = api_key if api_key is not None else settings.DATA_GOV_API_KEY
    if not key:
        raise OgdConfigError(
            "DATA_GOV_API_KEY is not configured; cannot query the OGD API."
        )
    rid = resource_id or settings.DATA_GOV_RESOURCE_ID or DEFAULT_RESOURCE_ID
    root = (base_url or settings.DATA_GOV_BASE_URL).rstrip("/")
    url = f"{root}/{rid}"
    req_timeout = timeout or settings.DATA_GOV_TIMEOUT
    size = min(page_size or settings.DATA_GOV_PAGE_SIZE, MAX_PAGE_SIZE)
    size = max(size, 1)
    target = max(min(limit_total, MAX_PAGES * size), 1)

    params = _filter_params(state, district, market, commodity, variety, grade)
    records: list[dict] = []
    offset = 0
    total: int | None = None
    last_page_full = False
    try:
        async with AsyncClient(timeout=req_timeout) as client:
            while len(records) < target:
                page_limit = min(size, target - len(records))
                query = {
                    "api-key": key,
                    "format": "json",
                    "offset": offset,
                    "limit": page_limit,
                    **params,
                }
                resp: Response = await client.get(url, params=query)
                if resp.status_code != 200:
                    raise OgdUpstreamError(
                        f"OGD API returned status {resp.status_code}."
                    )
                try:
                    payload = resp.json()
                except ValueError as exc:
                    raise OgdUpstreamError(
                        "OGD API returned a non-JSON response."
                    ) from exc
                page = payload.get("records") or []
                if not isinstance(page, list):
                    raise OgdUpstreamError("OGD API records payload is malformed.")
                if not page:
                    break
                records.extend(page)
                offset += len(page)
                last_page_full = len(page) >= page_limit
                raw_total = payload.get("total")
                if isinstance(raw_total, int):
                    total = raw_total
                elif isinstance(raw_total, str) and raw_total.isdigit():
                    total = int(raw_total)
                if total is not None and offset >= total:
                    break
                if not last_page_full:
                    break
    except OgdUpstreamError:
        raise
    except HTTPError as exc:
        logger.warning("ogd_request_failed", error=str(exc), state=state)
        raise OgdUpstreamError(f"OGD request failed: {exc}") from exc

    truncated = len(records) >= target and (
        last_page_full or (total is not None and total > offset)
    )
    logger.info(
        "ogd_fetch_completed",
        state=state,
        district=district,
        commodity=commodity,
        count=len(records),
        truncated=truncated,
    )
    return records, truncated
