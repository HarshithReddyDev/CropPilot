from pydantic import BaseModel


class MarketDataSourceResponse(BaseModel):
    code: str
    name: str
    organization: str = ""
    category: str = ""
    base_url: str = ""
    source_type: str = ""
    access_type: str = ""
    attribution_text: str = ""
    enabled: bool = False
    status: str = "INVESTIGATE"
    provides: list[str] = []

    model_config = {"from_attributes": True}
