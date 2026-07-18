import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class DiseaseLog(Base):
    __tablename__ = "disease_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    plot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    h3_spatial_index: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    detected_disease: Mapped[str] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    detections: Mapped[dict] = mapped_column(JSONB, default=list)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    severity: Mapped[str] = mapped_column(String(50), default="unknown")
    recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    is_resolved: Mapped[bool] = mapped_column(default=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    plot = relationship("Plot", back_populates="disease_logs")
    detections_rel = relationship("DiseaseDetection", back_populates="disease_log", cascade="all, delete-orphan")


class DiseaseDetection(Base):
    __tablename__ = "disease_detections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    disease_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("disease_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_name: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox: Mapped[dict] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    disease_log = relationship("DiseaseLog", back_populates="detections_rel")
