from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.market import MarketPrice
from repositories.base import BaseRepository


def _norm(value: str | None) -> str:
    """Normalize nullable dimensions so the natural key deduplicates."""
    return value.strip() if value and value.strip() else ""


class MarketRepository(BaseRepository):
    def __init__(self):
        super().__init__(MarketPrice)

    def _conditions(
        self,
        district: str | None = None,
        market: str | None = None,
        commodity: str | None = None,
        state: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        partial: bool = False,
    ):
        def match(column, value: str):
            return (
                column.ilike(f"%{value}%") if partial else column.ilike(value)
            )

        conds = []
        if state:
            conds.append(match(MarketPrice.state, state))
        if district:
            conds.append(match(MarketPrice.district, district))
        if market:
            conds.append(match(MarketPrice.market, market))
        if commodity:
            conds.append(match(MarketPrice.commodity, commodity))
        if variety:
            conds.append(match(MarketPrice.variety, variety))
        if grade:
            conds.append(match(MarketPrice.grade, grade))
        return conds

    def _apply_filters(
        self,
        stmt,
        district: str | None = None,
        market: str | None = None,
        commodity: str | None = None,
        state: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
    ):
        return stmt.where(
            *self._conditions(
                district=district,
                market=market,
                commodity=commodity,
                state=state,
                variety=variety,
                grade=grade,
            )
        )

    async def query_prices(
        self,
        db: AsyncSession,
        commodity: str | None = None,
        state: str | None = None,
        market: str | None = None,
        district: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        days_back: int = 7,
        skip: int = 0,
        limit: int = 100,
    ):
        cutoff = date.today() - timedelta(days=days_back)
        stmt = select(MarketPrice).where(MarketPrice.arrival_date >= cutoff)
        stmt = stmt.where(
            *self._conditions(
                district=district,
                market=market,
                commodity=commodity,
                state=state,
                variety=variety,
                grade=grade,
                partial=True,
            )
        )
        stmt = (
            stmt.order_by(
                MarketPrice.arrival_date.desc(),
                MarketPrice.market.asc(),
                MarketPrice.commodity.asc(),
            )
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_commodity(
        self, db: AsyncSession, commodity: str, state: str
    ) -> list[MarketPrice]:
        stmt = (
            select(MarketPrice)
            .where(MarketPrice.commodity.ilike(commodity))
            .where(MarketPrice.state.ilike(state))
            .order_by(MarketPrice.arrival_date.desc())
            .limit(10)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_latest(
        self,
        db: AsyncSession,
        state: str | None = None,
        district: str | None = None,
        commodity: str | None = None,
        market: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MarketPrice]:
        """Most recent observation per (state, district, market, commodity,
        variety, grade).

        State None means national scope. "Latest" means the newest stored
        arrival_date per group, not the current wall-clock price.
        District is part of the grain: identical market names in different
        districts must never collapse. Deterministic ordering throughout;
        SQL groups, Python slices.
        """
        conds = self._conditions(
            district=district,
            market=market,
            commodity=commodity,
            state=state,
            variety=variety,
            grade=grade,
        )
        maxq = (
            select(
                MarketPrice.state.label("s"),
                MarketPrice.district.label("d"),
                MarketPrice.market.label("m"),
                MarketPrice.commodity.label("c"),
                MarketPrice.variety.label("v"),
                MarketPrice.grade.label("g"),
                func.max(MarketPrice.arrival_date).label("max_date"),
            )
            .where(*conds)
            .group_by(
                MarketPrice.state,
                MarketPrice.district,
                MarketPrice.market,
                MarketPrice.commodity,
                MarketPrice.variety,
                MarketPrice.grade,
            )
            .subquery()
        )
        stmt = (
            select(MarketPrice)
            .join(
                maxq,
                (MarketPrice.state == maxq.c.s)
                & (
                    func.coalesce(MarketPrice.district, "")
                    == func.coalesce(maxq.c.d, "")
                )
                & (MarketPrice.market == maxq.c.m)
                & (MarketPrice.commodity == maxq.c.c)
                & (
                    func.coalesce(MarketPrice.variety, "")
                    == func.coalesce(maxq.c.v, "")
                )
                & (
                    func.coalesce(MarketPrice.grade, "")
                    == func.coalesce(maxq.c.g, "")
                )
                & (MarketPrice.arrival_date == maxq.c.max_date),
            )
            .where(*conds)
        )
        result = await db.execute(stmt)
        rows = list(result.scalars().all())
        # Deterministic tie-break when a group has several rows on its
        # newest date; then global ordering and pagination.
        newest: dict[tuple, MarketPrice] = {}
        for row in sorted(
            rows, key=lambda r: (r.created_at is None, r.created_at), reverse=True
        ):
            key = (
                row.state,
                row.district or "",
                row.market,
                row.commodity,
                row.variety or "",
                row.grade or "",
            )
            newest.setdefault(key, row)
        ordered = sorted(
            newest.values(),
            key=lambda r: (
                -r.arrival_date.toordinal(),
                r.state,
                r.district or "",
                r.market,
                r.commodity,
                r.variety or "",
                r.grade or "",
            ),
        )
        return ordered[offset : offset + limit]

    async def get_history(
        self,
        db: AsyncSession,
        state: str | None = None,
        commodity: str = "",
        district: str | None = None,
        market: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        days: int = 30,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[MarketPrice]:
        cutoff = from_date or (date.today() - timedelta(days=days))
        stmt = select(MarketPrice).where(MarketPrice.arrival_date >= cutoff)
        if to_date:
            stmt = stmt.where(MarketPrice.arrival_date <= to_date)
        stmt = self._apply_filters(
            stmt,
            district=district,
            market=market,
            commodity=commodity,
            state=state,
            variety=variety,
            grade=grade,
        )
        stmt = stmt.order_by(MarketPrice.arrival_date.asc(), MarketPrice.market.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_comparison(
        self,
        db: AsyncSession,
        state: str | None = None,
        commodity: str = "",
        district: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
    ) -> list[MarketPrice]:
        """Latest observation per market for one commodity lineage.

        Rows carry their own variety/grade/unit so callers only compare
        within a compatible group; the query never averages across groups.
        """
        return await self.get_latest(
            db,
            state=state,
            district=district,
            commodity=commodity,
            variety=variety,
            grade=grade,
            limit=500,
        )

    async def distinct_values(
        self,
        db: AsyncSession,
        column: str,
        state: str | None = None,
        district: str | None = None,
        market: str | None = None,
        commodity: str | None = None,
        variety: str | None = None,
        grade: str | None = None,
        limit: int = 1000,
    ) -> list[str]:
        col = getattr(MarketPrice, column)
        stmt = select(col)
        if state:
            stmt = stmt.where(MarketPrice.state.ilike(state))
        if district:
            stmt = stmt.where(MarketPrice.district.ilike(district))
        if market:
            stmt = stmt.where(MarketPrice.market.ilike(market))
        if commodity:
            stmt = stmt.where(MarketPrice.commodity.ilike(commodity))
        if variety:
            stmt = stmt.where(MarketPrice.variety.ilike(variety))
        if grade:
            stmt = stmt.where(MarketPrice.grade.ilike(grade))
        stmt = stmt.where(col.is_not(None)).where(col != "")
        stmt = stmt.distinct().order_by(col.asc()).limit(limit)
        result = await db.execute(stmt)
        return [row for row in result.scalars().all() if row]

    async def get_observation_bounds(
        self, db: AsyncSession, state: str | None = None
    ) -> tuple[date | None, date | None, int]:
        stmt = select(
            func.min(MarketPrice.arrival_date),
            func.max(MarketPrice.arrival_date),
            func.count(),
        )
        if state:
            stmt = stmt.where(MarketPrice.state.ilike(state))
        result = await db.execute(stmt)
        row = result.one()
        return row[0], row[1], row[2] or 0

    async def get_overview(
        self, db: AsyncSession, state: str | None = None
    ) -> dict:
        """Cheap national/state overview via SQL aggregation only."""
        filters = []
        if state:
            filters.append(MarketPrice.state.ilike(state))
        states = (
            await db.execute(
                select(func.count(func.distinct(MarketPrice.state))).where(*filters)
            )
        ).scalar() or 0
        markets = (
            await db.execute(
                select(func.count(func.distinct(MarketPrice.market))).where(*filters)
            )
        ).scalar() or 0
        commodities = (
            await db.execute(
                select(func.count(func.distinct(MarketPrice.commodity))).where(
                    *filters
                )
            )
        ).scalar() or 0
        bounds = (
            await db.execute(
                select(
                    func.min(MarketPrice.arrival_date),
                    func.max(MarketPrice.arrival_date),
                ).where(*filters)
            )
        ).one()
        return {
            "states_reporting": states,
            "markets_reporting": markets,
            "commodities_reported": commodities,
            "oldest_observation_date": bounds[0],
            "latest_observation_date": bounds[1],
        }

    async def find_by_natural_key(
        self,
        db: AsyncSession,
        state: str,
        district: str | None,
        market: str,
        commodity: str,
        variety: str | None,
        grade: str | None,
        arrival: date,
    ) -> MarketPrice | None:
        # Coalesce both sides so pre-backfill legacy NULL rows still match
        # the normalized "" key instead of silently duplicating.
        stmt = (
            select(MarketPrice)
            .where(MarketPrice.state == state)
            .where(func.coalesce(MarketPrice.district, "") == _norm(district))
            .where(MarketPrice.market == market)
            .where(MarketPrice.commodity == commodity)
            .where(func.coalesce(MarketPrice.variety, "") == _norm(variety))
            .where(func.coalesce(MarketPrice.grade, "") == _norm(grade))
            .where(MarketPrice.arrival_date == arrival)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def store_observation(
        self,
        db: AsyncSession,
        state: str,
        district: str | None,
        market: str,
        commodity: str,
        variety: str | None,
        grade: str | None,
        arrival: date,
        min_price: float,
        max_price: float,
        modal_price: float,
        price_per_unit: str,
        source: str = "AGMARKNET",
        source_resource_id: str | None = None,
        raw_record: dict | None = None,
        arrivals: float | None = None,
        arrival_unit: str | None = None,
    ) -> tuple[MarketPrice, bool]:
        """Idempotent store. Returns (row, stored True / duplicate False)."""
        existing = await self.find_by_natural_key(
            db, state, district, market, commodity, variety, grade, arrival
        )
        if existing is not None:
            return existing, False
        row = await self.create(
            db,
            state=state,
            district=_norm(district),
            market=market,
            commodity=commodity,
            variety=_norm(variety),
            grade=_norm(grade),
            arrival_date=arrival,
            min_price=min_price,
            max_price=max_price,
            modal_price=modal_price,
            price_per_unit=price_per_unit,
            source=source,
            source_resource_id=source_resource_id,
            raw_record=raw_record or {},
            arrivals=arrivals,
            arrival_unit=arrival_unit,
        )
        return row, True


market_repository = MarketRepository()
