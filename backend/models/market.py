import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    commodity: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    variety: Mapped[str] = mapped_column(String(255), nullable=True)
    market: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    district: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    min_price: Mapped[float] = mapped_column(Float, nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    modal_price: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_unit: Mapped[str] = mapped_column(String(50), default="INR/quintal")
    arrival_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), default="AGMARKNET")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
