"""Async client for AGMARKNET Direct (public web backend).

Backend only. The tested public endpoints require no API key, cookies,
session, or CSRF. They do require browser-like headers or the upstream
nginx layer answers 403. See AGMARKNET reference: the public site at
https://agmarknet.gov.in/home is a frontend over this backend.

Returns upstream payloads parsed but otherwise uncoerced; see
`services.market_providers` for normalization into canonical observations.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import structlog
from httpx import AsyncClient, HTTPError, Response

from core.config import settings

logger = structlog.get_logger(__name__)

BROWSER_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://agmarknet.gov.in",
    "Referer": "https://agmarknet.gov.in/",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
}


class AgmarknetError(RuntimeError):
    """Base error for the AGMARKNET Direct provider."""


class AgmarknetHTTPError(AgmarknetError):
    """Non-2xx response or transport failure upstream."""


class AgmarknetResponseError(AgmarknetError):
    """2xx response that is not usable JSON (e.g. Django 500 HTML page)."""


class AgmarknetNoDataError(AgmarknetError):
    """Upstream answered successfully but reports no data for the query."""


def format_report_date(value: date) -> str:
    """Central date formatter. The backend accepts YYYY-MM-DD.

    DD/MM/YYYY provably crashes the upstream Django view (HTTP 500 HTML),
    so every caller must go through this function.
    """
    return value.isoformat()


def _is_no_data(payload: Any) -> bool:
    if isinstance(payload, dict):
        if payload.get("success") is False:
            return True
        message = str(payload.get("message", "")).lower()
        return "no data" in message or "no arrivals" in message
    return False


async def _request(
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: int | None = None,
) -> Any:
    root = settings.AGMARKNET_BASE_URL.rstrip("/")
    url = f"{root}/{path.lstrip('/')}"
    req_timeout = timeout or settings.AGMARKNET_TIMEOUT
    try:
        async with AsyncClient(timeout=req_timeout, headers=BROWSER_HEADERS) as client:
            resp: Response = await client.request(
                method, url, params=params, json=json_body
            )
    except HTTPError as exc:
        logger.warning("agmarknet_request_failed", path=path, error=str(exc))
        raise AgmarknetHTTPError(f"AGMARKNET request failed: {exc}") from exc
    if resp.status_code != 200:
        raise AgmarknetHTTPError(
            f"AGMARKNET returned status {resp.status_code} for {path}."
        )
    content_type = resp.headers.get("content-type", "")
    if "application/json" not in content_type:
        raise AgmarknetResponseError(
            f"AGMARKNET returned non-JSON content for {path}."
        )
    try:
        payload = resp.json()
    except ValueError as exc:
        raise AgmarknetResponseError(
            f"AGMARKNET returned malformed JSON for {path}."
        ) from exc
    if _is_no_data(payload):
        raise AgmarknetNoDataError(f"AGMARKNET reports no data for {path}.")
    return payload


async def fetch_filters() -> dict[str, Any]:
    """Metadata bundle: commodities, groups, states, districts, markets,
    varieties, grades, report types, date-range restrictions."""
    payload = await _request("GET", "/daily-price-arrival/filters")
    if not isinstance(payload, dict):
        raise AgmarknetResponseError("Filter payload is malformed.")
    return payload


async def list_states(page: int = 1) -> dict[str, Any]:
    payload = await _request("GET", "/location/state", params={"page": page})
    if not isinstance(payload, dict):
        raise AgmarknetResponseError("State payload is malformed.")
    return payload


async def fetch_all_states() -> list[dict[str, Any]]:
    """All state entries across paginated responses, excluding the
    synthetic 'All States/UTs' selector entry."""
    states: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = await list_states(page=page)
        batch = payload.get("states") or []
        if not isinstance(batch, list):
            raise AgmarknetResponseError("State list payload is malformed.")
        states.extend(batch)
        pagination = payload.get("pagination") or {}
        total_pages = pagination.get("total_pages")
        if not batch:
            break
        if not isinstance(total_pages, int):
            break
        if page >= total_pages:
            break
        page += 1
        if page > 100:
            raise AgmarknetResponseError("State pagination did not terminate.")
    return [
        s for s in states
        if isinstance(s, dict) and "all" not in str(s.get("state_name", "")).lower()
    ]


async def list_market_categories() -> Any:
    return await _request("GET", "/list-market-category")


async def daily_state_report(report_date: date, state_id: int | str) -> dict[str, Any]:
    """Commodity-wise, market-wise daily report for one state and date."""
    payload = await _request(
        "GET",
        "/prices-and-arrivals/commodity-market/daily-report-state",
        params={
            "date": format_report_date(report_date),
            "state": state_id,
            "includeExcel": "false",
        },
    )
    if not isinstance(payload, dict):
        raise AgmarknetResponseError("Daily report payload is malformed.")
    return payload


async def market_daily_report(
    report_date: date, market_ids: list[int | str], state_ids: list[int | str]
) -> dict[str, Any]:
    """Market-wise, commodity-wise daily report (includes grade column)."""
    payload = await _request(
        "POST",
        "/prices-and-arrivals/market-report/daily",
        json_body={
            "date": format_report_date(report_date),
            "marketIds": list(market_ids),
            "stateIds": list(state_ids),
            "includeExcel": False,
        },
    )
    if not isinstance(payload, dict):
        raise AgmarknetResponseError("Market report payload is malformed.")
    return payload
