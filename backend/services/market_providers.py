"""Market data provider boundary.

Source API -> provider -> canonical OGD-shaped record -> existing
normalization (`services.market_normalization`) -> repository -> API.

Only AGMARKNET Direct is wired into the production path. The OGD client
remains dormant for future use.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import structlog

from services import agmarknet_client
from services.agmarknet_client import AgmarknetNoDataError

logger = structlog.get_logger(__name__)

PROVIDER_NAME = "AGMARKNET-direct"
SOURCE_NAME = "AGMARKNET"
SOURCE_URL = "https://agmarknet.gov.in/"


@dataclass(frozen=True)
class ProviderState:
    id: int | str
    name: str


@dataclass(frozen=True)
class MarketRef:
    market_id: int | str | None
    market_name: str
    district_id: int | str | None
    district_name: str
    state_id: int | str | None
    state_name: str


def _strip(value: object) -> str:
    return str(value).strip() if value is not None else ""


class AgmarknetDirectProvider:
    name = PROVIDER_NAME
    source_name = SOURCE_NAME
    source_url = SOURCE_URL

    async def get_states(self) -> list[ProviderState]:
        raw = await agmarknet_client.fetch_all_states()
        states = []
        for entry in raw:
            try:
                states.append(
                    ProviderState(id=entry["id"], name=_strip(entry["state_name"]))
                )
            except (KeyError, TypeError):
                logger.warning("agmarknet_state_skipped", entry=str(entry)[:150])
        return sorted(states, key=lambda s: s.name)

    async def get_state_id(self, state_name: str) -> int | str | None:
        wanted = state_name.strip().lower()
        for state in await self.get_states():
            if state.name.lower() == wanted:
                return state.id
        return None

    async def get_market_index(self) -> dict[str, MarketRef]:
        """Map stripped market name -> district/state reference.

        Built from AGMARKNET metadata IDs, never guessed from strings.
        """
        payload = await agmarknet_client.fetch_filters()
        data = payload.get("data", {})
        districts = {
            d.get("id"): _strip(d.get("district_name"))
            for d in data.get("district_data", [])
            if isinstance(d, dict)
        }
        states = {
            s.get("state_id"): _strip(s.get("state_name"))
            for s in data.get("state_data", [])
            if isinstance(s, dict)
        }
        index: dict[str, MarketRef] = {}
        for entry in data.get("market_data", []):
            if not isinstance(entry, dict):
                continue
            name = _strip(entry.get("mkt_name"))
            if not name or "all markets" in name.lower():
                continue
            district_id = entry.get("district_id")
            state_id = entry.get("state_id")
            # First entry wins; metadata may repeat markets across contexts.
            index.setdefault(
                name,
                MarketRef(
                    market_id=entry.get("id"),
                    market_name=name,
                    district_id=district_id,
                    district_name=districts.get(district_id, ""),
                    state_id=state_id,
                    state_name=states.get(state_id, ""),
                ),
            )
        return index

    async def daily_observations(
        self,
        report_date: date,
        state: ProviderState,
        market_index: dict[str, MarketRef] | None = None,
    ) -> list[dict]:
        """Fetch one state-day report and map rows to canonical records.

        Returns OGD-shaped dicts (state, district, market, commodity,
        variety, grade, arrival_date, min/max/modal_price, unit) ready for
        the shared normalization layer. Grade is "" when the endpoint does
        not provide one; never invented.
        """
        try:
            payload = await agmarknet_client.daily_state_report(report_date, state.id)
        except AgmarknetNoDataError:
            logger.info(
                "agmarknet_no_data", state=state.name, date=report_date.isoformat()
            )
            return []
        if market_index is None:
            market_index = await self.get_market_index()
        arrival = report_date.isoformat()
        records: list[dict] = []
        for group in payload.get("commodityGroups", []):
            if not isinstance(group, dict):
                continue
            for commodity in group.get("commodities", []):
                if not isinstance(commodity, dict):
                    continue
                commodity_name = _strip(commodity.get("commodityName"))
                if not commodity_name:
                    continue
                for market in commodity.get("markets", []):
                    if not isinstance(market, dict):
                        continue
                    market_name = _strip(market.get("marketCenter"))
                    if not market_name:
                        continue
                    ref = market_index.get(market_name)
                    if ref is None:
                        logger.warning(
                            "agmarknet_market_unresolved",
                            market=market_name,
                            state=state.name,
                        )
                    for row in market.get("data", []):
                        if not isinstance(row, dict):
                            continue
                        records.append(
                            {
                                "state": state.name,
                                "district": ref.district_name if ref else "",
                                "market": market_name,
                                "commodity": commodity_name,
                                "variety": _strip(row.get("variety")),
                                "grade": _strip(row.get("grade")),
                                "arrival_date": arrival,
                                "min_price": row.get("minimumPrice"),
                                "max_price": row.get("maximumPrice"),
                                "modal_price": row.get("modalPrice"),
                                "unit": row.get("unitOfPrice") or "Rs./Quintal",
                                "arrivals": row.get("arrivals"),
                                "unitOfArrivals": row.get("unitOfArrivals"),
                            }
                        )
        return records


agmarknet_provider = AgmarknetDirectProvider()
