from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from repositories.user import user_repository
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    async def register(
        self, db: AsyncSession, request: RegisterRequest
    ) -> TokenResponse:
        existing = await user_repository.get_by_email(db, request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        if request.phone:
            existing_phone = await user_repository.get_by_phone(db, request.phone)
            if existing_phone:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Phone already registered",
                )

        user = await user_repository.create(
            db,
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            phone=request.phone,
            state=request.state,
            district=request.district,
        )

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        await user_repository.update_refresh_token(
            db, user.id, refresh_token
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def login(
        self, db: AsyncSession, request: LoginRequest
    ) -> TokenResponse:
        user = await user_repository.get_by_email(db, request.email)
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        await user_repository.update_refresh_token(
            db, user.id, refresh_token
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_token(
        self, db: AsyncSession, refresh_token: str
    ) -> TokenResponse:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = await user_repository.get_by_id(db, int(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"role": user.role},
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        await user_repository.update_refresh_token(
            db, user.id, new_refresh_token
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, db: AsyncSession, user_id: str):
        await user_repository.update_refresh_token(db, user_id, None)
