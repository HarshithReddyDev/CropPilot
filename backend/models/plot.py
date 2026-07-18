import uuid
from datetime import datetime, timezone

from geoalchemy2 import Geography
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Plot(Base):
    __tablename__ = "plots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    crop_type: Mapped[str] = mapped_column(String(100), nullable=True)
    crop_variety: Mapped[str] = mapped_column(String(100), nullable=True)
    sowing_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    expected_harvest_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    area_hectares: Mapped[float] = mapped_column(Float, default=0.0)
    geometry: Mapped[str] = mapped_column(Geography(geometry_type="POLYGON", srid=4326), nullable=True)
    centroid: Mapped[str] = mapped_column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    h3_index: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    h3_resolution: Mapped[int] = mapped_column(Integer, default=8)
    soil_ph: Mapped[float] = mapped_column(Float, nullable=True)
    soil_moisture: Mapped[float] = mapped_column(Float, nullable=True)
    irrigation_type: Mapped[str] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="active", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    farm = relationship("Farm", back_populates="plots")
    farmer = relationship("User", back_populates="plots")
    disease_logs = relationship("DiseaseLog", back_populates="plot", cascade="all, delete-orphan")
