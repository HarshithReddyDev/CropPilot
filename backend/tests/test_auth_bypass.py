"""Development auth bypass safety tests.

Production must always fail closed; development may serve a deterministic
identity only when explicitly enabled outside production.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.config import settings
from core.dependencies import DEV_USER_ID, get_current_user


@pytest_asyncio.fixture
async def auth_session():
    from db.base import Base
    from models.user import User

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,  # type: ignore[arg-type]
            tables=[User.__table__],  # type: ignore[list-item]
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


async def test_production_requires_auth_even_with_flag(auth_session, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", True)
    assert settings.dev_auth_bypass_active is False
    with pytest.raises(Exception) as exc_info:
        await get_current_user(None, auth_session)
    assert getattr(exc_info.value, "status_code", None) == 401


async def test_development_bypass_disabled_by_default(auth_session, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", False)
    assert settings.dev_auth_bypass_active is False
    with pytest.raises(Exception) as exc_info:
        await get_current_user(None, auth_session)
    assert getattr(exc_info.value, "status_code", None) == 401


async def test_development_bypass_returns_deterministic_user(auth_session, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", True)
    assert settings.dev_auth_bypass_active is True
    first = await get_current_user(None, auth_session)
    second = await get_current_user(None, auth_session)
    assert first.id == DEV_USER_ID == second.id
    assert first.is_active is True
    assert first.email == "dev@croppilot.local"
    # The dev identity is transient: never written to the database.
    from models.user import User
    from sqlalchemy import select

    stored = await auth_session.scalar(select(User).where(User.id == DEV_USER_ID))
    assert stored is None


async def test_development_bypass_still_rejects_bad_token(auth_session, monkeypatch):
    from fastapi.security import HTTPAuthorizationCredentials

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", True)
    bad = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-jwt")
    with pytest.raises(Exception) as exc_info:
        await get_current_user(bad, auth_session)
    assert getattr(exc_info.value, "status_code", None) == 401


async def test_markets_endpoint_open_in_dev_bypass(monkeypatch):
    from httpx import ASGITransport, AsyncClient

    from core.dependencies import get_db
    from db.base import Base
    from main import app
    from models.market_geo import GeoDistrict, GeoMarket, GeoState

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        from models.market import MarketIngestion, MarketPrice

        await conn.run_sync(
            Base.metadata.create_all,  # type: ignore[arg-type]
            tables=[  # type: ignore[list-item]
                GeoState.__table__,
                GeoDistrict.__table__,
                GeoMarket.__table__,
                MarketPrice.__table__,
                MarketIngestion.__table__,
            ],
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", True)
    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/markets/meta/states")
    finally:
        app.dependency_overrides.clear()
    await engine.dispose()
    assert response.status_code == 200
