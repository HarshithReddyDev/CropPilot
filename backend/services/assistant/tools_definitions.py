"""Assistant tool registration. Declares each tool once.

Input validation is Pydantic (unknown args rejected by the registry).
Executors are deterministic Python over service layers: no raw SQL,
no shell, no arbitrary HTTP. Auth-gated tools check context.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from services.assistant.tools_disease import crop_profit, disease_log_summary
from services.assistant.tools_market import (
    list_commodities,
    list_districts,
    list_grades,
    list_markets,
    list_states,
    list_varieties,
    market_compare,
    market_history,
    market_latest,
    market_overview,
)
from services.assistant.tools_registry import ToolDefinition, tool_registry
from services.assistant.tools_schemes import scheme_search, schemes_list
from services.assistant.tools_weather import weather_current, weather_forecast


class MarketFilter(BaseModel):
    model_config = {"extra": "forbid"}

    commodity: str
    state: Optional[str] = None
    district: Optional[str] = None
    market: Optional[str] = None
    variety: Optional[str] = None
    grade: Optional[str] = None


class LatestInput(MarketFilter):
    limit: int = Field(default=5, ge=1, le=10)


class HistoryInput(MarketFilter):
    days: int = Field(default=30, ge=1, le=90)


class CompareInput(BaseModel):
    model_config = {"extra": "forbid"}

    commodity: str
    state: Optional[str] = None
    district: Optional[str] = None
    variety: Optional[str] = None
    grade: Optional[str] = None


class OverviewInput(BaseModel):
    model_config = {"extra": "forbid"}

    state: Optional[str] = None


class MetaScopeInput(BaseModel):
    """Shared optional scope for metadata/entity-resolution tools."""

    model_config = {"extra": "forbid"}

    state: Optional[str] = None
    district: Optional[str] = None
    market: Optional[str] = None
    commodity: Optional[str] = None
    variety: Optional[str] = None


class H3Input(BaseModel):
    model_config = {"extra": "forbid"}

    h3_index: str


class SchemeListInput(BaseModel):
    model_config = {"extra": "forbid"}

    state: Optional[str] = None
    category: Optional[str] = None


class SchemeSearchInput(BaseModel):
    model_config = {"extra": "forbid"}

    query: str
    state: Optional[str] = None


class DiseaseLogInput(BaseModel):
    model_config = {"extra": "forbid"}

    log_id: str


class ProfitInput(BaseModel):
    model_config = {"extra": "forbid"}

    crop: str
    area_hectares: float = Field(ge=0)
    expected_yield_per_hectare: float = Field(ge=0)
    market_price_per_quintal: float = Field(ge=0)
    cost_per_hectare: float = Field(ge=0)


async def _passthrough(func, args: dict, _ctx: dict) -> dict:
    """Call executor with only the validated args it actually accepts.

    Lets broad scope models (MetaScopeInput) feed narrow executors
    without per-tool key-picking lambdas.
    """
    import inspect

    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return await func(**args)
    accepted = {
        k: v for k, v in args.items() if k in params and v is not None
    }
    return await func(**accepted)


async def _disease_log(args: dict, ctx: dict) -> dict:
    if not ctx.get("user_id"):
        return {"ok": False, "error": "sign in required to read detection logs"}
    return await disease_log_summary(**args)


def _register() -> None:
    tools: list[tuple[ToolDefinition, Any]] = [
        (
            ToolDefinition(
                name="market_latest",
                description=(
                    "Latest mandi prices for a commodity. Defaults to Telangana. "
                    "Use when the farmer asks current rates. "
                    "state takes an Indian STATE name (e.g. Telangana); a "
                    "district name (e.g. Nalgonda) goes in district, never in state."
                ),
                input_schema=LatestInput,
                capability="market",
                family="market",
                audit_event="assistant.market_latest",
            ),
            lambda a, c: _passthrough(market_latest, a, c),
        ),
        (
            ToolDefinition(
                name="market_history",
                description="Price history series for a commodity over past days. "
                "state is a STATE name; district names go in district.",
                input_schema=HistoryInput,
                capability="market",
                family="market",
                audit_event="assistant.market_history",
            ),
            lambda a, c: _passthrough(market_history, a, c),
        ),
        (
            ToolDefinition(
                name="market_compare",
                description="Compare latest modal prices across markets for a commodity.",
                input_schema=CompareInput,
                capability="market",
                family="market",
                audit_event="assistant.market_compare",
            ),
            lambda a, c: _passthrough(market_compare, a, c),
        ),
        (
            ToolDefinition(
                name="market_overview",
                description="Coverage overview: counts and date bounds.",
                input_schema=OverviewInput,
                capability="market",
                family="market",
                audit_event="assistant.market_overview",
            ),
            lambda a, c: _passthrough(market_overview, a, c),
        ),
        (
            ToolDefinition(
                name="market_list_states",
                description="All reporting states. Use to resolve state names.",
                input_schema=MetaScopeInput,
                capability="market",
                family="market",
            ),
            lambda a, c: _passthrough(list_states, a, c),
        ),
        (
            ToolDefinition(
                name="market_list_districts",
                description="Districts in scope, optionally filtered by state.",
                input_schema=MetaScopeInput,
                capability="market",
                family="market",
            ),
            lambda a, c: _passthrough(list_districts, a, c),
        ),
        (
            ToolDefinition(
                name="market_list_markets",
                description="Markets in scope for optional state/district/commodity.",
                input_schema=MetaScopeInput,
                capability="market",
                family="market",
            ),
            lambda a, c: _passthrough(list_markets, a, c),
        ),
        (
            ToolDefinition(
                name="market_list_commodities",
                description="Commodities in scope for optional state/district/market.",
                input_schema=MetaScopeInput,
                capability="market",
                family="market",
            ),
            lambda a, c: _passthrough(list_commodities, a, c),
        ),
        (
            ToolDefinition(
                name="market_list_varieties",
                description="Varieties in scope for optional filters.",
                input_schema=MetaScopeInput,
                capability="market",
                family="market",
            ),
            lambda a, c: _passthrough(list_varieties, a, c),
        ),
        (
            ToolDefinition(
                name="market_list_grades",
                description="Grades in scope for optional filters.",
                input_schema=MetaScopeInput,
                capability="market",
                family="market",
            ),
            lambda a, c: _passthrough(list_grades, a, c),
        ),
        (
            ToolDefinition(
                name="weather_current",
                description="Stored current weather for an H3 cell index.",
                input_schema=H3Input,
                capability="weather",
                family="weather",
            ),
            lambda a, c: _passthrough(weather_current, a, c),
        ),
        (
            ToolDefinition(
                name="weather_forecast",
                description="Stored forecast for an H3 cell index.",
                input_schema=H3Input,
                capability="weather",
                family="weather",
            ),
            lambda a, c: _passthrough(weather_forecast, a, c),
        ),
        (
            ToolDefinition(
                name="schemes_list",
                description="Browse the schemes catalog by state and/or category. For a named scheme or a topic question, prefer scheme_search. Leave state empty unless the user named a state.",
                input_schema=SchemeListInput,
                capability="schemes",
                family="schemes",
            ),
            lambda a, c: _passthrough(schemes_list, a, c),
        ),
        (
            ToolDefinition(
                name="scheme_search",
                description="Search scheme documents by scheme name, topic, or question (e.g. PMFBY, crop insurance subsidy). Returns matches with citations. Leave state empty unless the user named a state.",
                input_schema=SchemeSearchInput,
                capability="schemes",
                family="schemes",
            ),
            lambda a, c: _passthrough(scheme_search, a, c),
        ),
        (
            ToolDefinition(
                name="disease_log_summary",
                description="Summarize one of the farmer's vision detection logs by id.",
                input_schema=DiseaseLogInput,
                capability="disease",
                family="disease",
                auth_scope="user",
                audit_event="assistant.disease_log",
            ),
            _disease_log,
        ),
        (
            ToolDefinition(
                name="crop_profit",
                description="Expected profit arithmetic for a crop plan.",
                input_schema=ProfitInput,
                capability="planning",
                family="planning",
            ),
            lambda a, c: _passthrough(crop_profit, a, c),
        ),
    ]
    for definition, executor in tools:
        if tool_registry.get(definition.name) is None:
            tool_registry.register(definition, executor)


_register()

assistant_tools = tool_registry
