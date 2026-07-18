from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.plot import plot_repository
from schemas.plot import PlotCreate, PlotResponse, PlotUpdate


class PlotService:
    async def create_plot(
        self, db: AsyncSession, farmer_id: UUID, data: PlotCreate
    ) -> PlotResponse:
        from geoalchemy2.shape import from_shape
        from shapely.geometry import shape

        create_data = data.model_dump(exclude={"geometry", "centroid"})
        create_data["farmer_id"] = farmer_id

        if data.geometry:
            geom_shape = shape(data.geometry)
            create_data["geometry"] = from_shape(geom_shape, srid=4326)
        if data.centroid:
            cent_shape = shape(data.centroid)
            create_data["centroid"] = from_shape(cent_shape, srid=4326)

        plot = await plot_repository.create(db, **create_data)
        return PlotResponse.model_validate(plot)

    async def get_plot(self, db: AsyncSession, plot_id: UUID) -> PlotResponse:
        plot = await plot_repository.get_by_id(db, plot_id)
        if not plot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")
        return PlotResponse.model_validate(plot)

    async def get_plots_by_farmer(
        self, db: AsyncSession, farmer_id: UUID
    ) -> list[PlotResponse]:
        plots = await plot_repository.get_plots_by_farmer(db, farmer_id)
        return [PlotResponse.model_validate(p) for p in plots]

    async def get_plots_by_farm(
        self, db: AsyncSession, farm_id: UUID
    ) -> list[PlotResponse]:
        plots = await plot_repository.get_plots_by_farm(db, farm_id)
        return [PlotResponse.model_validate(p) for p in plots]

    async def update_plot(
        self, db: AsyncSession, plot_id: UUID, data: PlotUpdate
    ) -> PlotResponse:
        update_data = data.model_dump(exclude_none=True, exclude={"geometry", "centroid"})
        if data.geometry:
            from geoalchemy2.shape import from_shape
            from shapely.geometry import shape
            update_data["geometry"] = from_shape(shape(data.geometry), srid=4326)
        if data.centroid:
            from geoalchemy2.shape import from_shape
            from shapely.geometry import shape
            update_data["centroid"] = from_shape(shape(data.centroid), srid=4326)

        plot = await plot_repository.update(db, plot_id, **update_data)
        if not plot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")
        return PlotResponse.model_validate(plot)

    async def delete_plot(self, db: AsyncSession, plot_id: UUID) -> None:
        deleted = await plot_repository.delete(db, plot_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plot not found")

    async def get_nearby_plots(
        self, db: AsyncSession, h3_index: str
    ) -> list[PlotResponse]:
        plots = await plot_repository.get_nearby_plots(db, h3_index)
        return [PlotResponse.model_validate(p) for p in plots]
