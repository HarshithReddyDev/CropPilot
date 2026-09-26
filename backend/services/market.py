from datetime import date, datetime, timezone

import structlog

from core.config import settings
from repositories.market import market_repository
from schemas.market import (
    ComparisonResponse,
    ComparisonRow,
    FreshnessInfo,
    HistoryPoint,
    HistoryResponse,
    HistoryStats,
    LatestPricesResponse,
    MarketOverview,
    MarketPriceQuery,
    MarketPriceResponse,
    MetaListResponse,
    SourceProvenance,
)
from services.market_normalization import SOURCE_NAME, normalize_record

logger = structlog.get_logger(__name__)

# Observations older than this are flagged stale in API responses.
STALE_AFTER_DAYS = 2


def _provenance() -> SourceProvenance:
    return SourceProvenance(
        resource_id=settings.AGMARKNET_BASE_URL,
        retrieved_at=datetime.now(timezone.utc),
    )


def _dedupe_names(values: list[str]) -> list[str]:
    """Drop repeated display names (distinct source IDs can share a name)."""
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def _freshness(rows: list, fallback_max: date | None = None) -> FreshnessInfo:
    dates = [r.arrival_date for r in rows if r.arrival_date]
    if dates:
        latest, oldest = max(dates), min(dates)
    elif fallback_max is not None:
        latest, oldest = fallback_max, fallback_max
    else:
        return FreshnessInfo()
    age = (date.today() - latest).days
    return FreshnessInfo(
        latest_observation_date=latest,
        oldest_observation_date=oldest,
        age_days=age,
        is_stale=age > STALE_AFTER_DAYS,
        observation_count=len(rows),
    )


class MarketService:
    async def query_prices(self, db, query: MarketPriceQuery):
        prices = await market_repository.query_prices(
            db,
            commodity=query.commodity,
            state=query.state,
            market=query.market,
            district=query.district,
            variety=query.variety,
            grade=query.grade,
            days_back=query.days_back,
        )
        return [MarketPriceResponse.model_validate(p) for p in prices]

    async def get_latest_price(self, db, commodity: str, state: str):
        """Legacy lookup. DB only; no network fallback."""
        prices = await market_repository.get_latest_by_commodity(db, commodity, state)
        return [MarketPriceResponse.model_validate(p) for p in prices]

    async def get_latest(
        self,
        db,
        state: str | None = None,
        district: str | None = None,
        commodity: str | None = None,
        market: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> LatestPricesResponse:
        rows = await market_repository.get_latest(
            db,
            state=state,
            district=district,
            commodity=commodity,
            market=market,
            variety=variety,
            grade=grade,
            limit=limit,
            offset=offset,
        )
        items = [MarketPriceResponse.model_validate(r) for r in rows]
        return LatestPricesResponse(
            items=items, provenance=_provenance(), freshness=_freshness(rows)
        )

    async def get_telangana_latest(
        self,
        db,
        district: str | None = None,
        commodity: str | None = None,
        market: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        limit: int = 100,
    ) -> LatestPricesResponse:
        """Compatibility wrapper. Prefer get_latest with explicit state."""
        return await self.get_latest(
            db,
            state="Telangana",
            district=district,
            commodity=commodity,
            market=market,
            variety=variety,
            grade=grade,
            limit=limit,
        )

    async def get_history(
        self,
        db,
        commodity: str,
        state: str | None = None,
        district: str | None = None,
        market: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        days: int = 30,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> HistoryResponse:
        rows = await market_repository.get_history(
            db,
            state=state,
            commodity=commodity,
            district=district,
            market=market,
            variety=variety,
            grade=grade,
            days=days,
            from_date=from_date,
            to_date=to_date,
        )
        # Pin to a single lineage (market + variety + grade + unit) taken
        # from the most recent observation so the series never averages
        # across incompatible groups.
        group_rows = rows
        if rows and (market is None or variety is None or grade is None):
            anchor = max(
                rows,
                key=lambda r: (
                    r.arrival_date,
                    r.created_at.isoformat() if r.created_at else "",
                ),
            )
            group_rows = [
                r
                for r in rows
                if r.market == anchor.market
                and (r.variety or "") == (anchor.variety or "")
                and (r.grade or "") == (anchor.grade or "")
                and r.price_per_unit == anchor.price_per_unit
            ]
        points = [
            HistoryPoint(
                arrival_date=r.arrival_date,
                min_price=r.min_price,
                max_price=r.max_price,
                modal_price=r.modal_price,
                market=r.market,
                variety=r.variety,
                grade=r.grade,
                price_per_unit=r.price_per_unit,
                arrivals=r.arrivals,
                arrival_unit=r.arrival_unit,
            )
            for r in sorted(group_rows, key=lambda r: r.arrival_date)
        ]
        modals = [p.modal_price for p in points]
        if modals:
            stats = HistoryStats(
                point_count=len(points),
                first_modal_price=modals[0],
                last_modal_price=modals[-1],
                change=modals[-1] - modals[0],
                change_percent=(
                    (modals[-1] - modals[0]) / modals[0] * 100 if modals[0] else None
                ),
                min_modal_price=min(modals),
                max_modal_price=max(modals),
            )
        else:
            stats = HistoryStats(point_count=0)
        return HistoryResponse(
            points=points,
            stats=stats,
            provenance=_provenance(),
            freshness=_freshness(rows),
        )

    async def get_telangana_history(
        self,
        db,
        commodity: str,
        district: str | None = None,
        market: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        days: int = 30,
    ) -> HistoryResponse:
        """Compatibility wrapper. Prefer get_history with explicit state."""
        return await self.get_history(
            db,
            commodity=commodity,
            state="Telangana",
            district=district,
            market=market,
            variety=variety,
            grade=grade,
            days=days,
        )

    async def get_comparison(
        self,
        db,
        commodity: str,
        state: str | None = None,
        district: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
    ) -> ComparisonResponse:
        rows = await market_repository.get_comparison(
            db,
            state=state,
            commodity=commodity,
            district=district,
            variety=variety,
            grade=grade,
        )
        # One row per market already; order deterministically by modal price.
        ordered = sorted(rows, key=lambda r: (r.modal_price, r.market))
        return ComparisonResponse(
            rows=[
                ComparisonRow(
                    market=r.market,
                    district=r.district,
                    state=r.state,
                    commodity=r.commodity,
                    variety=r.variety,
                    grade=r.grade,
                    min_price=r.min_price,
                    max_price=r.max_price,
                    modal_price=r.modal_price,
                    price_per_unit=r.price_per_unit,
                    arrival_date=r.arrival_date,
                    arrivals=r.arrivals,
                    arrival_unit=r.arrival_unit,
                    source=r.source,
                )
                for r in ordered
            ],
            group={
                "commodity": commodity,
                "state": state or "",
                "variety": variety or "",
                "grade": grade or "",
                "note": (
                    "Compare only rows with matching variety, grade, and unit."
                ),
            },
            provenance=_provenance(),
            freshness=_freshness(rows),
        )

    async def get_telangana_comparison(
        self,
        db,
        commodity: str,
        district: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
    ) -> ComparisonResponse:
        """Compatibility wrapper. Prefer get_comparison with explicit state."""
        return await self.get_comparison(
            db,
            commodity=commodity,
            state="Telangana",
            district=district,
            variety=variety,
            grade=grade,
        )

    async def get_states(self, db) -> MetaListResponse:
        from repositories.market_geo import geo_repository

        rows = await geo_repository.list_states(db)
        if rows:
            return MetaListResponse(
                values=_dedupe_names([r.name for r in rows]), provenance=_provenance()
            )
        values = await market_repository.distinct_values(db, "state")
        return MetaListResponse(values=_dedupe_names(values), provenance=_provenance())

    async def get_districts(
        self, db, state: str | None = None
    ) -> MetaListResponse:
        from repositories.market_geo import geo_repository

        rows = await geo_repository.list_districts(db, state_name=state)
        if rows:
            return MetaListResponse(
                values=_dedupe_names([r.name for r in rows]), provenance=_provenance()
            )
        values = await market_repository.distinct_values(db, "district", state=state)
        return MetaListResponse(values=_dedupe_names(values), provenance=_provenance())

    async def get_commodities(
        self,
        db,
        state: str | None = None,
        district: str | None = None,
        market: str | None = None,
    ) -> MetaListResponse:
        values = await market_repository.distinct_values(
            db, "commodity", state=state, district=district, market=market
        )
        return MetaListResponse(values=_dedupe_names(values), provenance=_provenance())

    async def get_markets(
        self,
        db,
        state: str | None = None,
        district: str | None = None,
        commodity: str | None = None,
    ) -> MetaListResponse:
        from repositories.market_geo import geo_repository

        # Catalog-backed when no commodity filter: every market in scope,
        # regardless of ingested prices. Commodity scoping stays
        # price-driven since the catalog does not track commodities.
        if commodity is None:
            rows = await geo_repository.list_markets(
                db, state_name=state, district_name=district
            )
            if rows:
                return MetaListResponse(
                    values=_dedupe_names([r.name for r in rows]), provenance=_provenance()
                )
        values = await market_repository.distinct_values(
            db,
            "market",
            state=state,
            district=district,
            commodity=commodity,
        )
        return MetaListResponse(values=_dedupe_names(values), provenance=_provenance())

    async def get_varieties(
        self,
        db,
        state: str | None = None,
        district: str | None = None,
        market: str | None = None,
        commodity: str | None = None,
    ) -> MetaListResponse:
        values = await market_repository.distinct_values(
            db,
            "variety",
            state=state,
            district=district,
            market=market,
            commodity=commodity,
        )
        return MetaListResponse(values=_dedupe_names(values), provenance=_provenance())

    async def get_grades(
        self,
        db,
        state: str | None = None,
        district: str | None = None,
        market: str | None = None,
        commodity: str | None = None,
        variety: str | None = None,
    ) -> MetaListResponse:
        values = await market_repository.distinct_values(
            db,
            "grade",
            state=state,
            district=district,
            market=market,
            commodity=commodity,
            variety=variety,
        )
        return MetaListResponse(values=_dedupe_names(values), provenance=_provenance())

    async def get_overview(
        self, db, state: str | None = None
    ) -> MarketOverview:
        data = await market_repository.get_overview(db, state=state)
        return MarketOverview(provenance=_provenance(), **data)

    # ---- compatibility wrappers (Telangana-scoped first generation) ----

    async def get_telangana_districts(self, db) -> MetaListResponse:
        return await self.get_districts(db, state="Telangana")

    async def get_telangana_commodities(
        self, db, district: str | None = None
    ) -> MetaListResponse:
        return await self.get_commodities(
            db, state="Telangana", district=district
        )

    async def get_telangana_markets(
        self, db, district: str | None = None, commodity: str | None = None
    ) -> MetaListResponse:
        return await self.get_markets(
            db, state="Telangana", district=district, commodity=commodity
        )

    async def ingest_records(
        self,
        db,
        raw_records: list[dict],
        resource_id: str | None = None,
        state_filter: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> tuple[int, int, date | None, date | None]:
        """Normalize + idempotently store raw OGD records.

        Returns (stored, skipped, min_date, max_date). Malformed records
        and records outside the optional date range count as skipped,
        never as fabricated rows.
        """
        stored, skipped = 0, 0
        min_seen: date | None = None
        max_seen: date | None = None
        rid = resource_id or settings.DATA_GOV_RESOURCE_ID
        for raw in raw_records:
            obs, reason = normalize_record(raw if isinstance(raw, dict) else {})
            if obs is None:
                skipped += 1
                logger.info("market_record_skipped", reason=reason)
                continue
            if start_date and obs.arrival_date < start_date:
                skipped += 1
                continue
            if end_date and obs.arrival_date > end_date:
                skipped += 1
                continue
            if obs.arrival_date:
                min_seen = (
                    obs.arrival_date
                    if min_seen is None or obs.arrival_date < min_seen
                    else min_seen
                )
                max_seen = (
                    obs.arrival_date
                    if max_seen is None or obs.arrival_date > max_seen
                    else max_seen
                )
            _, created = await market_repository.store_observation(
                db,
                state=obs.state,
                district=obs.district,
                market=obs.market,
                commodity=obs.commodity,
                variety=obs.variety,
                grade=obs.grade,
                arrival=obs.arrival_date,
                min_price=float(obs.min_price),
                max_price=float(obs.max_price),
                modal_price=float(obs.modal_price),
                price_per_unit=obs.price_per_unit,
                source=SOURCE_NAME,
                source_resource_id=rid,
                raw_record=raw if isinstance(raw, dict) else {},
                arrivals=float(obs.arrivals) if obs.arrivals is not None else None,
                arrival_unit=obs.arrival_unit,
            )
            if created:
                stored += 1
            else:
                skipped += 1
        return stored, skipped, min_seen, max_seen


market_service = MarketService()
