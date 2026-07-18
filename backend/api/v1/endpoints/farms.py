from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.farm import FarmCreate, FarmResponse, FarmUpdate
from services.farm import farm_service

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("", response_model=FarmResponse, status_code=201)
async def create_farm(
    data: FarmCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await farm_service.create_farm(db, current_user.id, data)


@router.get("", response_model=list[FarmResponse])
async def list_farms(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await farm_service.get_farms_by_farmer(db, current_user.id)


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await farm_service.get_farm(db, farm_id)


@router.patch("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: UUID,
    data: FarmUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await farm_service.update_farm(db, farm_id, data)


@router.delete("/{farm_id}", status_code=204)
async def delete_farm(
    farm_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await farm_service.delete_farm(db, farm_id)
