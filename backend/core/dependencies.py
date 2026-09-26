from uuid import UUID
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.security import decode_token
from db.session import async_session_factory
from models.user import User
from repositories.user import user_repository

security_scheme = HTTPBearer(auto_error=False)

# Deterministic identity used ONLY by the development auth bypass.
# It is never written to the database and never valid in production.
DEV_USER_ID = UUID("00000000-0000-4000-8000-000000000000")


def _dev_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=DEV_USER_ID,
        email="dev@croppilot.local",
        password_hash="!",
        full_name="Development",
        role="farmer",
        state=None,
        district=None,
        is_active=True,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None:
        # Development-only bypass: no credentials are accepted, fabricated,
        # or validated here. Production (ENVIRONMENT=production) always
        # falls through to the 401 below, even if the flag is set.
        if settings.dev_auth_bypass_active:
            return _dev_user()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    user = await user_repository.get_by_id(db, UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def get_current_active_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
