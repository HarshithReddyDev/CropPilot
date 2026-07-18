from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.market import MarketPriceQuery, MarketPriceResponse
from services.market import market_service

router = APIRouter(prefix="/markets", tags=["Market Prices"])


@router.get("/prices", response_model=list[MarketPriceResponse])
async def query_prices(
    commodity: str | None = Query(None),
    state: str | None = Query(None),
    market: str | None = Query(None),
    days_back: int = Query(7, ge=1, le=365),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    query = MarketPriceQuery(
        commodity=commodity,
        state=state,
        market=market,
        days_back=days_back,
    )
    return await market_service.query_prices(db, query)


@router.get("/prices/latest", response_model=list[MarketPriceResponse])
async def get_latest_prices(
    commodity: str = Query(...),
    state: str = Query(...),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await market_service.get_latest_price(db, commodity, state)
