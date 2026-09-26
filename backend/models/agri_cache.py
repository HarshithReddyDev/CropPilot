"""Cache tables for agricultural intelligence providers.

Soil changes slowly (30-day TTL), district crop mixes change seasonally
(7-day TTL). Every row carries source + version + fetch time so stale data
can never look current. Raw provider payloads are never stored — only the
normalized values the panel displays.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from models.market import JSON_VARIANT


class SoilCache(Base):
    __tablename__ = "soil_cache"
    __table_args__ = (
        UniqueConstraint("lat_key", "lng_key", "property", "depth",
                         name="uq_soil_cache_cell_prop"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lat_key: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    lng_key: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    property: Mapped[str] = mapped_column(String(32), nullable=False)
    depth: Mapped[str] = mapped_column(String(16), nullable=False, default="0-5cm")
    mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="soilgrids/wcs")
    source_version: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CropContextCache(Base):
    __tablename__ = "crop_context_cache"
    __table_args__ = (UniqueConstraint("district", "state", name="uq_crop_ctx_district"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON_VARIANT, nullable=False, default=dict)
    data_year: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="agmarknet")
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
