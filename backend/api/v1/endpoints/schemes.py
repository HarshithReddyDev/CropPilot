from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.scheme import GovernmentSchemeResponse
from services.scheme import scheme_service

router = APIRouter(prefix="/schemes", tags=["Government Schemes"])


@router.get("", response_model=list[GovernmentSchemeResponse])
async def get_schemes(
    state: str | None = Query(None),
    category: str | None = Query(None),
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if category:
        return await scheme_service.get_schemes_by_category(db, category)
    return await scheme_service.get_schemes_by_state(db, state or "Telangana")
