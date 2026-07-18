from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.plot import PlotCreate, PlotResponse, PlotUpdate
from services.plot import plot_service

router = APIRouter(prefix="/plots", tags=["Plots"])


@router.post("", response_model=PlotResponse, status_code=201)
async def create_plot(
    data: PlotCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await plot_service.create_plot(db, current_user.id, data)


@router.get("", response_model=list[PlotResponse])
async def list_plots(
    farm_id: UUID | None = Query(None),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if farm_id:
        return await plot_service.get_plots_by_farm(db, farm_id)
    return await plot_service.get_plots_by_farmer(db, current_user.id)


@router.get("/nearby", response_model=list[PlotResponse])
async def get_nearby_plots(
    h3_index: str = Query(...),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await plot_service.get_nearby_plots(db, h3_index)


@router.get("/{plot_id}", response_model=PlotResponse)
async def get_plot(
    plot_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await plot_service.get_plot(db, plot_id)


@router.patch("/{plot_id}", response_model=PlotResponse)
async def update_plot(
    plot_id: UUID,
    data: PlotUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await plot_service.update_plot(db, plot_id, data)


@router.delete("/{plot_id}", status_code=204)
async def delete_plot(
    plot_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    await plot_service.delete_plot(db, plot_id)
