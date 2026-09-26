from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import structlog

from core.config import settings

logger = structlog.get_logger(__name__)

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
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return
    except Exception as exc:
        # Partial initialization is a development-only fallback for local
        # databases without PostGIS (plain PostgreSQL), where geo-dependent
        # tables cannot be created. Production must fail loudly instead of
        # booting with a silently partial schema.
        logger.warning("init_db_full_failed", error=str(exc)[:300])
        if settings.ENVIRONMENT.strip().lower() == "production":
            raise
    for table in Base.metadata.sorted_tables:
        try:
            async with engine.begin() as conn:
                async with conn.begin_nested():
                    await conn.run_sync(table.create, checkfirst=True)
        except Exception as exc:
            logger.warning(
                "init_db_table_skipped", table=table.name, error=str(exc)[:300]
            )
