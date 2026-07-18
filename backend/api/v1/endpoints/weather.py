from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.weather import WeatherForecastResponse, WeatherRecordResponse
from services.weather import weather_service

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("/current", response_model=WeatherRecordResponse)
async def get_current_weather(
    h3_index: str = Query(...),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await weather_service.get_current_weather(db, h3_index)


@router.get("/forecast", response_model=WeatherForecastResponse)
async def get_forecast(
    h3_index: str = Query(...),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await weather_service.get_forecast(db, h3_index)
