from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    plot_id: UUID | None = None
    stream: bool = True


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    sources: list[dict] = Field(default_factory=list)


class RAGStreamRequest(BaseModel):
    query: str = Field(min_length=1)
    plot_id: UUID | None = None
    h3_index: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class RAGStreamEvent(BaseModel):
    event: str
    data: str


class IntelRequest(BaseModel):
    incident_id: UUID
    include_schemes: bool = True
    include_market_data: bool = True
    include_weather: bool = True
