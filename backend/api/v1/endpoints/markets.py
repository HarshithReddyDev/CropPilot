from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user
from core.dependencies import get_db
from models.user import User
from schemas.market import (
    ComparisonResponse,
    HistoryResponse,
    LatestPricesResponse,
    MarketOverview,
    MarketPriceQuery,
    MarketPriceResponse,
    MetaListResponse,
)
from services.market import market_service

router = APIRouter(prefix="/markets", tags=["Market Prices"])


@router.get("/prices", response_model=list[MarketPriceResponse])
async def query_prices(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    commodity: str | None = Query(None),
    state: str | None = Query(None),
    market: str | None = Query(None),
    district: str | None = Query(None),
    days_back: int = Query(7, ge=1, le=365),
):
    query = MarketPriceQuery(
        commodity=commodity,
        state=state,
        market=market,
        district=district,
        days_back=days_back,
    )
    return await market_service.query_prices(db, query)


@router.get("/prices/latest", response_model=list[MarketPriceResponse])
async def get_latest_prices(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    commodity: str = Query(...),
    state: str = Query(...),
):
    return await market_service.get_latest_price(db, commodity, state)


@router.get("/latest", response_model=LatestPricesResponse)
async def get_latest(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    state: str | None = Query(None),
    district: str | None = Query(None),
    commodity: str | None = Query(None),
    market: str | None = Query(None),
    variety: str | None = Query(None),
    grade: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return await market_service.get_latest(
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


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    commodity: str = Query(...),
    state: str | None = Query(None),
    district: str | None = Query(None),
    market: str | None = Query(None),
    variety: str | None = Query(None),
    grade: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
):
    return await market_service.get_history(
        db,
        commodity=commodity,
        state=state,
        district=district,
        market=market,
        variety=variety,
        grade=grade,
        days=days,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/comparison", response_model=ComparisonResponse)
async def get_comparison(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    commodity: str = Query(...),
    state: str | None = Query(None),
    district: str | None = Query(None),
    variety: str | None = Query(None),
    grade: str | None = Query(None),
):
    return await market_service.get_comparison(
        db,
        commodity=commodity,
        state=state,
        district=district,
        variety=variety,
        grade=grade,
    )


@router.get("/overview", response_model=MarketOverview)
async def get_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    state: str | None = Query(None),
):
    return await market_service.get_overview(db, state=state)


@router.get("/meta/states", response_model=MetaListResponse)
async def get_meta_states(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await market_service.get_states(db)


@router.get("/meta/districts", response_model=MetaListResponse)
async def get_meta_districts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    state: str | None = Query(None),
):
    return await market_service.get_districts(db, state=state)


@router.get("/meta/commodities", response_model=MetaListResponse)
async def get_meta_commodities(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    state: str | None = Query(None),
    district: str | None = Query(None),
    market: str | None = Query(None),
):
    return await market_service.get_commodities(
        db, state=state, district=district, market=market
    )


@router.get("/meta/markets", response_model=MetaListResponse)
async def get_meta_markets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    state: str | None = Query(None),
    district: str | None = Query(None),
    commodity: str | None = Query(None),
):
    return await market_service.get_markets(
        db, state=state, district=district, commodity=commodity
    )


@router.get("/meta/varieties", response_model=MetaListResponse)
async def get_meta_varieties(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    state: str | None = Query(None),
    district: str | None = Query(None),
    market: str | None = Query(None),
    commodity: str | None = Query(None),
):
    return await market_service.get_varieties(
        db, state=state, district=district, market=market, commodity=commodity
    )


@router.get("/meta/grades", response_model=MetaListResponse)
async def get_meta_grades(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    state: str | None = Query(None),
    district: str | None = Query(None),
    market: str | None = Query(None),
    commodity: str | None = Query(None),
    variety: str | None = Query(None),
):
    return await market_service.get_grades(
        db,
        state=state,
        district=district,
        market=market,
        commodity=commodity,
        variety=variety,
    )


# ---- compatibility: first-generation Telangana-scoped routes ----


@router.get("/telangana/latest", response_model=LatestPricesResponse)
async def get_telangana_latest(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    district: str | None = Query(None),
    commodity: str | None = Query(None),
    market: str | None = Query(None),
    variety: str | None = Query(None),
    grade: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    return await market_service.get_telangana_latest(
        db,
        district=district,
        commodity=commodity,
        market=market,
        variety=variety,
        grade=grade,
        limit=limit,
    )


@router.get("/telangana/history", response_model=HistoryResponse)
async def get_telangana_history(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    commodity: str = Query(...),
    district: str | None = Query(None),
    market: str | None = Query(None),
    variety: str | None = Query(None),
    grade: str | None = Query(None),
    days: int = Query(30, ge=1, le=365),
):
    return await market_service.get_telangana_history(
        db,
        commodity=commodity,
        district=district,
        market=market,
        variety=variety,
        grade=grade,
        days=days,
    )


@router.get("/telangana/comparison", response_model=ComparisonResponse)
async def get_telangana_comparison(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    commodity: str = Query(...),
    district: str | None = Query(None),
    variety: str | None = Query(None),
    grade: str | None = Query(None),
):
    return await market_service.get_telangana_comparison(
        db,
        commodity=commodity,
        district=district,
        variety=variety,
        grade=grade,
    )


@router.get("/telangana/meta/districts", response_model=MetaListResponse)
async def get_telangana_districts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await market_service.get_telangana_districts(db)


@router.get("/telangana/meta/commodities", response_model=MetaListResponse)
async def get_telangana_commodities(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    district: str | None = Query(None),
):
    return await market_service.get_telangana_commodities(db, district=district)


@router.get("/telangana/meta/markets", response_model=MetaListResponse)
async def get_telangana_markets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    district: str | None = Query(None),
    commodity: str | None = Query(None),
):
    return await market_service.get_telangana_markets(
        db, district=district, commodity=commodity
    )
