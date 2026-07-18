from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.disease import DiseaseLogResponse, VisionSyncRequest
from services.disease import disease_service

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post("/vision-sync", response_model=DiseaseLogResponse, status_code=201)
async def vision_sync(
    payload: VisionSyncRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    return await disease_service.sync_vision(db, current_user.id, payload)
