import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password, verify_password
from models.user import User
from schemas.auth import LoginRequest, RegisterRequest
from services.auth import AuthService


@pytest.mark.asyncio
async def test_password_hashing():
    password = "securePassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrongPassword", hashed)


@pytest.mark.asyncio
async def test_auth_register(test_session: AsyncSession):
    service = AuthService()
    request = RegisterRequest(
        email="new@test.in",
        password="password123",
        full_name="New User",
        state="Karnataka",
    )
    result = await service.register(test_session, request)
    assert result.access_token is not None
    assert result.refresh_token is not None


@pytest.mark.asyncio
async def test_auth_login(test_session: AsyncSession):
    service = AuthService()
    register_req = RegisterRequest(
        email="login@test.in",
        password="password123",
        full_name="Login User",
    )
    await service.register(test_session, register_req)

    login_req = LoginRequest(email="login@test.in", password="password123")
    result = await service.login(test_session, login_req)
    assert result.access_token is not None


@pytest.mark.asyncio
async def test_model_creation(test_session: AsyncSession):
    user = User(
        email="model@test.in",
        password_hash=hash_password("test123"),
        full_name="Model Test",
        role="farmer",
    )
    test_session.add(user)
    await test_session.flush()
    assert user.id is not None
    assert user.is_active is True
    assert user.role == "farmer"
