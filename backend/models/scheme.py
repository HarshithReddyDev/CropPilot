import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class GovernmentScheme(Base):
    __tablename__ = "government_schemes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    scheme_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    scheme_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ministry: Mapped[str] = mapped_column(String(255), nullable=True)
    department: Mapped[str] = mapped_column(String(255), nullable=True)
    state_jurisdiction: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    eligibility_criteria: Mapped[str] = mapped_column(Text, nullable=True)
    benefits: Mapped[str] = mapped_column(Text, nullable=True)
    application_process: Mapped[str] = mapped_column(Text, nullable=True)
    documents_required: Mapped[str] = mapped_column(Text, nullable=True)
    funding_pattern: Mapped[str] = mapped_column(String(255), nullable=True)
    beneficiary_type: Mapped[str] = mapped_column(String(100), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[dict] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    website_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
