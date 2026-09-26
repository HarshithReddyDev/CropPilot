import asyncio
from db.session import async_session_factory
from sqlalchemy import text

async def m():
    async with async_session_factory() as db:
        r = (await db.execute(text("select distinct commodity from market_prices where commodity ilike '%paddy%' order by 1"))).all()
        print('paddy-like commodities:', r)
        r2 = (await db.execute(text("select state,count(*) from market_prices where commodity ilike '%paddy%' group by 1 order by 2 desc limit 8"))).all()
        print('paddy by state:', r2)
        r3 = (await db.execute(text("select count(*) from market_prices where state ilike 'Telangana'"))).scalar()
        print('telangana total:', r3)

asyncio.run(m())
