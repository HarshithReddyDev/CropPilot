from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: UUID
    email: str
    phone: str | None
    full_name: str
    role: str
    state: str | None
    district: str | None
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    state: str | None = None
    district: str | None = None
