from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from core.config import settings

_pool_kwargs = {}
if settings.DEBUG:
    _pool_kwargs["poolclass"] = NullPool
else:
    _pool_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    _pool_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    _pool_kwargs["pool_pre_ping"] = settings.DATABASE_POOL_PRE_PING

engine = create_async_engine(
    settings.db_url,
    echo=settings.DEBUG,
    **_pool_kwargs,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def init_db():
    from db.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
