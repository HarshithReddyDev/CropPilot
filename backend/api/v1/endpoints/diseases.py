from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.disease import DiseaseLogResponse
from services.disease import disease_service

router = APIRouter(prefix="/diseases", tags=["Diseases"])


@router.get("/{log_id}", response_model=DiseaseLogResponse)
async def get_disease_log(
    log_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await disease_service.get_disease_log(db, log_id)


@router.get("/plot/{plot_id}", response_model=list[DiseaseLogResponse])
async def get_plot_disease_logs(
    plot_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await disease_service.get_logs_by_plot(db, plot_id)
