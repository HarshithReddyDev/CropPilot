import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "CropPilot"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@croppilot.in",
            "password": "password123",
            "full_name": "Test Farmer",
            "state": "Telangana",
            "district": "Hyderabad",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    return data


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    await test_register_user(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@croppilot.in",
            "password": "password123",
            "full_name": "Test Farmer",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await test_register_user(client)
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@croppilot.in",
            "password": "password123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@test.in",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_profile(client: AsyncClient):
    auth = await test_register_user(client)
    token = auth["access_token"]
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@croppilot.in"
