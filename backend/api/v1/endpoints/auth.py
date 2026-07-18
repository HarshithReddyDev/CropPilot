from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_current_user, get_db
from models.user import User
from schemas.auth import LoginRequest, RefreshTokenRequest, RegisterRequest, TokenResponse
from services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.register(db, request)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.login(db, request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await auth_service.refresh_token(db, request.refresh_token)


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await auth_service.logout(db, str(current_user.id))
    return {"message": "Logged out successfully"}
