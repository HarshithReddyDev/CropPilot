"""Source registry reads and provider capability declarations.

Capabilities describe what each provider actually supplies. Statuses:
IMPLEMENTED (live and wired), INVESTIGATE (access unknown), REQUIRES_ACCESS
(registration/empanelment), LICENSED (paid feed), NOT_PRACTICAL (no stable
public interface), DUPLICATE (derived from another integrated source).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.market_sources import MarketDataSource
from schemas.market_sources import MarketDataSourceResponse

CAPABILITIES: dict[str, dict[str, object]] = {
    "AGMARKNET": {
        "status": "IMPLEMENTED",
        "provides": [
            "mandi price", "arrivals", "state", "district", "market",
            "commodity", "variety", "grade", "date",
        ],
    },
    "ENAM": {
        "status": "REQUIRES_ACCESS",
        "provides": [
            "auction/trade observations", "APMC", "commodity",
            "quantity/arrival where available", "trade/auction price",
            "quality/assaying fields where available",
        ],
        "note": "Integration is via SFAC empanelment; no public API found.",
    },
    "DCA_PMD": {
        "status": "NOT_PRACTICAL",
        "provides": ["retail price", "wholesale price", "reporting centre", "commodity", "date"],
        "note": "ASP.NET WebForms reports only; no stable public API found.",
    },
    "DES_AGRI": {
        "status": "NOT_PRACTICAL",
        "provides": ["wholesale price", "retail price", "farm harvest price", "international price", "statistical series"],
        "note": "HTML dashboard tables and publications only; no stable public API found.",
    },
    "STATE_APMC": {
        "status": "INVESTIGATE",
        "provides": ["state-specific mandi data where published"],
        "note": "Inventory per state required before building adapters.",
    },
    "TRADESTAT": {
        "status": "NOT_PRACTICAL",
        "provides": ["imports", "exports", "HS code", "country/region", "month", "value", "quantity"],
        "note": "Interactive form-driven portal; no documented public API found.",
    },
    "NCDEX": {
        "status": "LICENSED",
        "provides": ["exchange instrument", "contract", "OHLC", "volume", "open interest"],
        "note": "Detailed feeds are licensed products; no public API found.",
    },
    "MCX": {
        "status": "LICENSED",
        "provides": ["exchange instrument", "contract", "OHLC", "volume", "open interest", "spot where published"],
        "note": "Public pages are WAF-protected; detailed feeds are licensed products.",
    },
    "FCI": {
        "status": "NOT_PRACTICAL",
        "provides": ["procurement information", "stock information"],
        "note": "HTML pages only; no stable machine interface found.",
    },
    "CACP_MSP": {
        "status": "NOT_PRACTICAL",
        "provides": ["MSP notifications", "procurement prices", "marketing seasons"],
        "note": "Notifications published as documents; CACP site unreachable during discovery; no machine interface found.",
    },
}


async def list_sources(db: AsyncSession) -> list[MarketDataSourceResponse]:
    result = await db.execute(
        select(MarketDataSource).order_by(MarketDataSource.code.asc())
    )
    responses = []
    for row in result.scalars().all():
        caps = CAPABILITIES.get(row.code, {})
        provides = caps.get("provides", [])
        responses.append(
            MarketDataSourceResponse(
                code=row.code,
                name=row.name,
                organization=row.organization,
                category=row.category,
                base_url=row.base_url,
                source_type=row.source_type,
                access_type=row.access_type,
                attribution_text=row.attribution_text,
                enabled=row.enabled,
                status=str(caps.get("status", "INVESTIGATE")),
                provides=list(provides) if isinstance(provides, list) else [],
            )
        )
    return responses
