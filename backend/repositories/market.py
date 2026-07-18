from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.market import MarketPrice
from repositories.base import BaseRepository


class MarketRepository(BaseRepository):
    def __init__(self):
        super().__init__(MarketPrice)

    async def query_prices(
        self,
        db: AsyncSession,
        commodity: str | None = None,
        state: str | None = None,
        market: str | None = None,
        days_back: int = 7,
        skip: int = 0,
        limit: int = 100,
    ):
        cutoff = date.today() - timedelta(days=days_back)
        stmt = select(MarketPrice).where(MarketPrice.arrival_date >= cutoff)
        if commodity:
            stmt = stmt.where(MarketPrice.commodity.ilike(f"%{commodity}%"))
        if state:
            stmt = stmt.where(MarketPrice.state.ilike(f"%{state}%"))
        if market:
            stmt = stmt.where(MarketPrice.market.ilike(f"%{market}%"))
        stmt = stmt.order_by(MarketPrice.arrival_date.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

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
        return result.scalars().all()


market_repository = MarketRepository()
