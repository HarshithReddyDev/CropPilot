from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.plot import Plot
from repositories.base import BaseRepository


class PlotRepository(BaseRepository):
    def __init__(self):
        super().__init__(Plot)

    async def get_plots_by_farm(
        self, db: AsyncSession, farm_id: UUID
    ):
        stmt = select(Plot).where(Plot.farm_id == farm_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_plots_by_farmer(
        self, db: AsyncSession, farmer_id: UUID, skip: int = 0, limit: int = 100
    ):
        stmt = (
            select(Plot)
            .where(Plot.farmer_id == farmer_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_h3_index(
        self, db: AsyncSession, h3_index: str
    ):
        stmt = select(Plot).where(Plot.h3_index == h3_index)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_nearby_plots(
        self, db: AsyncSession, h3_index: str, resolution: int = 8
    ):
        from h3 import h3
        # h3-py 4.0+ uses grid_disk instead of k_ring
        neighbors = h3.grid_disk(h3_index, 1) if hasattr(h3, 'grid_disk') else h3.k_ring(h3_index, 1)
        stmt = select(Plot).where(Plot.h3_index.in_(list(neighbors)))
        result = await db.execute(stmt)
        plots = result.scalars().all()
        
        if not plots:
            # Fallback to PostGIS ST_DWithin (5km radius)
            try:
                lat, lng = h3.h3_to_geo(h3_index)
                fallback_stmt = select(Plot).where(
                    func.ST_DWithin(
                        Plot.centroid,
                        func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326),
                        5000  # meters
                    )
                )
                fallback_result = await db.execute(fallback_stmt)
                plots = fallback_result.scalars().all()
            except Exception:
                pass
                
        return plots


plot_repository = PlotRepository()
