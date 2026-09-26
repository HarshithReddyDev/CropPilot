from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.market_sources import MarketDataSourceResponse
from services.source_registry import list_sources

router = APIRouter(prefix="/market-data", tags=["Market Data Sources"])


@router.get("/sources", response_model=list[MarketDataSourceResponse])
async def get_market_data_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await list_sources(db)
