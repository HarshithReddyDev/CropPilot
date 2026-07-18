from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.farm import farm_repository
from schemas.farm import FarmCreate, FarmResponse, FarmUpdate


class FarmService:
    async def create_farm(
        self, db: AsyncSession, farmer_id: UUID, data: FarmCreate
    ) -> FarmResponse:
        farm = await farm_repository.create(
            db, farmer_id=farmer_id, **data.model_dump()
        )
        return FarmResponse.model_validate(farm)

    async def get_farm(self, db: AsyncSession, farm_id: UUID) -> FarmResponse:
        farm = await farm_repository.get_by_id(db, farm_id)
        if not farm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
        return FarmResponse.model_validate(farm)

    async def get_farms_by_farmer(
        self, db: AsyncSession, farmer_id: UUID
    ) -> list[FarmResponse]:
        farms = await farm_repository.get_farms_by_farmer(db, farmer_id)
        return [FarmResponse.model_validate(f) for f in farms]

    async def update_farm(
        self, db: AsyncSession, farm_id: UUID, data: FarmUpdate
    ) -> FarmResponse:
        farm = await farm_repository.update(
            db, farm_id, **data.model_dump(exclude_none=True)
        )
        if not farm:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
        return FarmResponse.model_validate(farm)

    async def delete_farm(self, db: AsyncSession, farm_id: UUID) -> None:
        deleted = await farm_repository.delete(db, farm_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")
