from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_refresh_token(
        self, db: AsyncSession, user_id: str, refresh_token: str | None
    ) -> User | None:
        return await self.update(db, user_id, refresh_token=refresh_token)


user_repository = UserRepository()
