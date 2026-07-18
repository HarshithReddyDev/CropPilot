from langchain_core.tools import tool
from typing import Any


@tool
def sql_query_tool(query: str) -> str:
    """Execute a SQL query against the market_prices table to get agricultural commodity prices.
    Input should be a valid SQL query string. Use this to answer questions about market prices."""
    from db.session import async_session_factory
    import asyncio

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_execute_sql(query))
        loop.close()
        return str(result)
    except Exception as e:
        return f"Error executing query: {e}"


async def _execute_sql(query: str) -> list[dict]:
    from sqlalchemy import text
    async with async_session_factory() as session:
        result = await session.execute(text(query))
        rows = result.fetchall()
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]


@tool
def scheme_semantic_search(query: str, state_jurisdiction: str = "Telangana") -> str:
    """Search government schemes using semantic vector search.
    Use this to find relevant government schemes for farmers."""
    from rag.pipeline import rag_pipeline
    import asyncio

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(
            rag_pipeline.hybrid_search_schemes(query, state_jurisdiction)
        )
        loop.close()
        return str(results)
    except Exception as e:
        return f"Error searching schemes: {e}"


@tool
def get_weather_data(h3_index: str) -> str:
    """Get current weather data for a given H3 spatial index.
    Useful for answering questions about weather conditions at a specific location."""
    from services.weather import weather_service
    from db.session import async_session_factory
    import asyncio

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_get_weather(h3_index))
        loop.close()
        return str(result)
    except Exception as e:
        return f"Weather data not found: {e}"


async def _get_weather(h3_index: str) -> dict:
    async with async_session_factory() as session:
        record = await weather_service.get_current_weather(session, h3_index)
        return record.model_dump() if record else {}


@tool
def get_forecast_data(h3_index: str) -> str:
    """Get weather forecast data for a given H3 spatial index."""
    from services.weather import weather_service
    from db.session import async_session_factory
    import asyncio

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_get_forecast(h3_index))
        loop.close()
        return str(result)
    except Exception as e:
        return f"Forecast data not found: {e}"


async def _get_forecast(h3_index: str) -> dict:
    async with async_session_factory() as session:
        forecast = await weather_service.get_forecast(session, h3_index)
        return forecast.model_dump() if forecast else {}


@tool
def get_disease_info(disease_name: str) -> str:
    """Get information about a specific crop disease, including symptoms and treatments."""
    disease_info = {
        "leaf_blast": {
            "name": "Leaf Blast",
            "symptoms": "Diamond-shaped lesions with gray centers and brown borders on leaves",
            "treatment": "Apply fungicides containing Tricyclazole or Carbendazim",
            "prevention": "Use resistant varieties, avoid excessive nitrogen",
        },
        "powdery_mildew": {
            "name": "Powdery Mildew",
            "symptoms": "White powdery coating on leaves and stems",
            "treatment": "Apply sulfur-based fungicides or potassium bicarbonate",
            "prevention": "Ensure good air circulation, avoid overhead watering",
        },
        "bacterial_blight": {
            "name": "Bacterial Blight",
            "symptoms": "Water-soaked lesions that turn brown, leaf wilting",
            "treatment": "Apply copper-based bactericides, remove infected plants",
            "prevention": "Use disease-free seeds, practice crop rotation",
        },
    }
    return str(disease_info.get(disease_name.lower().replace(" ", "_"), {
        "name": disease_name,
        "message": "Detailed information not available in knowledge base"
    }))


@tool
def calculate_profitability(
    crop: str, area_hectares: float, expected_yield_per_hectare: float,
    market_price_per_quintal: float, cost_per_hectare: float
) -> str:
    """Calculate expected profit for a crop given area, yield, price, and costs."""
    total_yield = area_hectares * expected_yield_per_hectare
    total_revenue = total_yield * market_price_per_quintal
    total_cost = area_hectares * cost_per_hectare
    profit = total_revenue - total_cost
    roi = ((profit / total_cost) * 100) if total_cost > 0 else 0
    return str({
        "total_yield_quintals": round(total_yield, 2),
        "total_revenue_inr": round(total_revenue, 2),
        "total_cost_inr": round(total_cost, 2),
        "profit_inr": round(profit, 2),
        "roi_percentage": round(roi, 2),
    })


agents_tools = [
    sql_query_tool,
    scheme_semantic_search,
    get_weather_data,
    get_forecast_data,
    get_disease_info,
    calculate_profitability,
]
