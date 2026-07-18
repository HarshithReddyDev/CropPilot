from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GovernmentSchemeResponse(BaseModel):
    id: UUID
    scheme_name: str
    scheme_code: str | None
    description: str
    ministry: str | None
    department: str | None
    state_jurisdiction: str | None
    eligibility_criteria: str | None
    benefits: str | None
    application_process: str | None
    documents_required: str | None
    funding_pattern: str | None
    beneficiary_type: str | None
    category: str | None
    tags: list
    is_active: bool
    website_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
