"""Source-backed geography catalog for Market Intelligence.

States/districts/markets come from AGMARKNET metadata synchronization,
independent of whether price observations have been ingested. Source IDs
are the stable identities; names are display-normalized (stripped) but
otherwise preserved verbatim.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class GeoState(Base):
    __tablename__ = "geo_states"
    __table_args__ = (UniqueConstraint("source_id", name="uq_geo_states_source"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class GeoDistrict(Base):
    __tablename__ = "geo_districts"
    __table_args__ = (UniqueConstraint("source_id", name="uq_geo_districts_source"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    state_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    state_name: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class GeoMarket(Base):
    __tablename__ = "geo_markets"
    __table_args__ = (UniqueConstraint("source_id", name="uq_geo_markets_source"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    district_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    district_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    state_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    state_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    # Geographic coordinates for the map marker layer. ALWAYS NULL unless a
    # verified source supplied them (coordinate_source records provenance,
    # e.g. "nominatim/osm"). Markets without coordinates stay in Market
    # Intelligence but are excluded from map markers — never invented.
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    coordinate_source: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    coordinates_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
