"""Repository for the source-backed geography catalog."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.market_geo import GeoDistrict, GeoMarket, GeoState
from repositories.base import BaseRepository


class GeoRepository(BaseRepository):
    def __init__(self):
        super().__init__(GeoState)

    async def upsert_state(
        self, db: AsyncSession, source_id: int, name: str
    ) -> tuple[GeoState, bool]:
        row = await db.scalar(select(GeoState).where(GeoState.source_id == source_id))
        if row is None:
            row = GeoState(source_id=source_id, name=name)
            db.add(row)
            await db.flush()
            return row, True
        if row.name != name:
            row.name = name
            row.updated_at = datetime.now(timezone.utc)
            await db.flush()
        return row, False

    async def upsert_district(
        self,
        db: AsyncSession,
        source_id: int,
        name: str,
        state_id: int,
        state_name: str,
    ) -> tuple[GeoDistrict, bool]:
        row = await db.scalar(
            select(GeoDistrict).where(GeoDistrict.source_id == source_id)
        )
        if row is None:
            row = GeoDistrict(
                source_id=source_id, name=name, state_id=state_id, state_name=state_name
            )
            db.add(row)
            await db.flush()
            return row, True
        changed = False
        for attr, value in (("name", name), ("state_id", state_id), ("state_name", state_name)):
            if getattr(row, attr) != value:
                setattr(row, attr, value)
                changed = True
        if changed:
            row.updated_at = datetime.now(timezone.utc)
            await db.flush()
        return row, changed

    async def upsert_market(
        self,
        db: AsyncSession,
        source_id: int,
        name: str,
        district_id: int | None,
        district_name: str,
        state_id: int | None,
        state_name: str,
        category: str = "",
    ) -> tuple[GeoMarket, bool]:
        row = await db.scalar(
            select(GeoMarket).where(GeoMarket.source_id == source_id)
        )
        if row is None:
            row = GeoMarket(
                source_id=source_id,
                name=name,
                district_id=district_id,
                district_name=district_name,
                state_id=state_id,
                state_name=state_name,
                category=category,
            )
            db.add(row)
            await db.flush()
            return row, True
        changed = False
        for attr, value in (
            ("name", name),
            ("district_id", district_id),
            ("district_name", district_name),
            ("state_id", state_id),
            ("state_name", state_name),
            ("category", category),
        ):
            if getattr(row, attr) != value:
                setattr(row, attr, value)
                changed = True
        if changed:
            row.updated_at = datetime.now(timezone.utc)
            await db.flush()
        return row, changed

    async def list_states(self, db: AsyncSession) -> list[GeoState]:
        result = await db.execute(select(GeoState).order_by(GeoState.name.asc()))
        return list(result.scalars().all())

    async def find_state(
        self, db: AsyncSession, state_name: str
    ) -> GeoState | None:
        wanted = state_name.strip().lower()
        result = await db.execute(select(GeoState))
        for row in result.scalars().all():
            if row.name.strip().lower() == wanted:
                return row
        return None

    async def list_districts(
        self, db: AsyncSession, state_name: str | None = None
    ) -> list[GeoDistrict]:
        stmt = select(GeoDistrict)
        if state_name:
            stmt = stmt.where(GeoDistrict.state_name.ilike(state_name))
        stmt = stmt.order_by(GeoDistrict.name.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def list_markets(
        self,
        db: AsyncSession,
        state_name: str | None = None,
        district_name: str | None = None,
        limit: int = 2000,
    ) -> list[GeoMarket]:
        stmt = select(GeoMarket)
        if state_name:
            stmt = stmt.where(GeoMarket.state_name.ilike(state_name))
        if district_name:
            stmt = stmt.where(GeoMarket.district_name.ilike(district_name))
        stmt = stmt.order_by(GeoMarket.name.asc()).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def counts(self, db: AsyncSession) -> dict[str, int]:
        states = (await db.execute(select(func.count()).select_from(GeoState))).scalar() or 0
        districts = (await db.execute(select(func.count()).select_from(GeoDistrict))).scalar() or 0
        markets = (await db.execute(select(func.count()).select_from(GeoMarket))).scalar() or 0
        return {"states": states, "districts": districts, "markets": markets}


geo_repository = GeoRepository()
