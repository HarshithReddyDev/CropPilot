from sqlalchemy.ext.asyncio import AsyncSession

from repositories.scheme import scheme_repository
from schemas.scheme import GovernmentSchemeResponse


class SchemeService:
    async def get_schemes_by_state(
        self, db: AsyncSession, state: str
    ) -> list[GovernmentSchemeResponse]:
        schemes = await scheme_repository.get_by_state(db, state)
        return [GovernmentSchemeResponse.model_validate(s) for s in schemes]

    async def get_schemes_by_category(
        self, db: AsyncSession, category: str
    ) -> list[GovernmentSchemeResponse]:
        schemes = await scheme_repository.get_by_category(db, category)
        return [GovernmentSchemeResponse.model_validate(s) for s in schemes]
