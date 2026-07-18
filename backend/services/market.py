from sqlalchemy.ext.asyncio import AsyncSession

from repositories.market import market_repository
from schemas.market import MarketPriceQuery, MarketPriceResponse


class MarketService:
    async def query_prices(
        self, db: AsyncSession, query: MarketPriceQuery
    ) -> list[MarketPriceResponse]:
        prices = await market_repository.query_prices(
            db,
            commodity=query.commodity,
            state=query.state,
            market=query.market,
            days_back=query.days_back,
        )
        return [MarketPriceResponse.model_validate(p) for p in prices]

    async def get_latest_price(
        self, db: AsyncSession, commodity: str, state: str
    ) -> list[MarketPriceResponse]:
        prices = await market_repository.get_latest_by_commodity(db, commodity, state)
        if not prices:
            # Fallback to fetching live data if not in DB
            fetched_price = await self.fetch_live_price(db, commodity, state)
            if fetched_price:
                return [fetched_price]
        return [MarketPriceResponse.model_validate(p) for p in prices]

    async def fetch_live_price(
        self, db: AsyncSession, commodity: str, state: str
    ) -> MarketPriceResponse | None:
        import httpx
        from datetime import datetime, timezone
        
        # Agmarknet API endpoint on data.gov.in
        # Requires API key from data.gov.in
        api_key = "YOUR_DATA_GOV_IN_API_KEY" 
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {
            "api-key": api_key,
            "format": "json",
            "filters[state]": state,
            "filters[commodity]": commodity,
            "limit": 1
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                
            if data and data.get("records") and len(data["records"]) > 0:
                record = data["records"][0]
                # Save to db
                db_record = await market_repository.create(
                    db,
                    state=record.get("state", state),
                    district=record.get("district", ""),
                    market=record.get("market", ""),
                    commodity=record.get("commodity", commodity),
                    variety=record.get("variety", ""),
                    arrival_date=datetime.now(timezone.utc).date(),
                    min_price=float(record.get("min_price", 0)),
                    max_price=float(record.get("max_price", 0)),
                    modal_price=float(record.get("modal_price", 0))
                )
                return MarketPriceResponse.model_validate(db_record)
        except Exception as e:
            # Fallback or log error
            print(f"Failed to fetch live Agmarknet data: {e}")
        return None

market_service = MarketService()
