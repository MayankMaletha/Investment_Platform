"""
tests/test_auth.py — Authentication endpoint tests.

Uses pytest-asyncio + httpx AsyncClient for async route testing.
Dependency overrides swap the real DB for an in-memory SQLite session.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from database.session import Base
from core.dependencies import get_db

# ─── In-Memory Test DB ────────────────────────────────────────────────────────

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ─── Test Data ────────────────────────────────────────────────────────────────

VALID_USER = {
    "email": "test@example.com",
    "username": "testuser",
    "password": "securepassword123",
    "full_name": "Test User",
    "risk_tolerance": "moderate",
}


# ─── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/api/v1/auth/register", json=VALID_USER)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == VALID_USER["email"]
    assert data["username"] == VALID_USER["username"]
    assert "id" in data
    assert "hashed_password" not in data  # Never leak password hash


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    await client.post("/api/v1/auth/register", json=VALID_USER)
    resp = await client.post("/api/v1/auth/register", json=VALID_USER)
    assert resp.status_code == 422
    assert "Email already registered" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_register_invalid_email(client):
    bad_user = {**VALID_USER, "email": "not-an-email"}
    resp = await client.post("/api/v1/auth/register", json=bad_user)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(client):
    bad_user = {**VALID_USER, "password": "short"}
    resp = await client.post("/api/v1/auth/register", json=bad_user)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client):
    await client.post("/api/v1/auth/register", json=VALID_USER)
    resp = await client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"],
        "password": VALID_USER["password"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json=VALID_USER)
    resp = await client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"],
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "anypassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client):
    await client.post("/api/v1/auth/register", json=VALID_USER)
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"],
        "password": VALID_USER["password"],
    })
    token = login_resp.json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == VALID_USER["email"]


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403  # No auth header


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_flow(client):
    await client.post("/api/v1/auth/register", json=VALID_USER)
    login = await client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"], "password": VALID_USER["password"]
    })
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # New refresh token should differ from old
    assert data["refresh_token"] != refresh_token


@pytest.mark.asyncio
async def test_refresh_token_reuse_rejected(client):
    """Refresh token rotation: reusing a consumed token should fail."""
    await client.post("/api/v1/auth/register", json=VALID_USER)
    login = await client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"], "password": VALID_USER["password"]
    })
    refresh_token = login.json()["refresh_token"]

    # Use once — should succeed
    await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    # Use again — should fail
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client):
    await client.post("/api/v1/auth/register", json=VALID_USER)
    login = await client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"], "password": VALID_USER["password"]
    })
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert resp.status_code == 204

    # Refresh after logout should fail
    resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp2.status_code == 401
