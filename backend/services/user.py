from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user import user_repository
from schemas.user import UserResponse, UserUpdate


class UserService:
    async def get_profile(self, db: AsyncSession, user_id: UUID) -> UserResponse:
        user = await user_repository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)

    async def update_profile(
        self, db: AsyncSession, user_id: UUID, update: UserUpdate
    ) -> UserResponse:
        user = await user_repository.update(
            db, user_id, **update.model_dump(exclude_none=True)
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)
