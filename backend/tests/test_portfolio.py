"""tests/test_portfolio.py — Portfolio management endpoint tests."""

import pytest
import pytest_asyncio
from decimal import Decimal
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from database.session import Base
from core.dependencies import get_db

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


@pytest_asyncio.fixture
async def auth_headers(client):
    """Register + login, return auth headers."""
    await client.post("/api/v1/auth/register", json={
        "email": "portfolio@test.com", "username": "portfoliouser",
        "password": "testpassword123", "risk_tolerance": "moderate",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "portfolio@test.com", "password": "testpassword123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_portfolios_returns_default(client, auth_headers):
    """Registration auto-creates a default portfolio."""
    resp = await client.get("/api/v1/portfolio/", headers=auth_headers)
    assert resp.status_code == 200
    portfolios = resp.json()
    assert len(portfolios) >= 1


@pytest.mark.asyncio
async def test_create_portfolio(client, auth_headers):
    resp = await client.post("/api/v1/portfolio/", headers=auth_headers, json={
        "name": "Growth Portfolio",
        "description": "High-growth tech stocks",
        "initial_cash": "10000.00",
        "currency": "USD",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Growth Portfolio"
    assert float(data["cash_balance"]) == 10000.0


@pytest.mark.asyncio
async def test_get_portfolio_by_id(client, auth_headers):
    create = await client.post("/api/v1/portfolio/", headers=auth_headers, json={
        "name": "Test Portfolio", "initial_cash": "5000",
    })
    portfolio_id = create.json()["id"]
    resp = await client.get(f"/api/v1/portfolio/{portfolio_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == portfolio_id


@pytest.mark.asyncio
async def test_get_nonexistent_portfolio_returns_404(client, auth_headers):
    resp = await client.get("/api/v1/portfolio/nonexistent-id", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_buy_asset(client, auth_headers):
    portfolios = await client.get("/api/v1/portfolio/", headers=auth_headers)
    portfolio_id = portfolios.json()[0]["id"]

    resp = await client.post(f"/api/v1/portfolio/{portfolio_id}/buy", headers=auth_headers, json={
        "symbol": "AAPL",
        "asset_type": "stock",
        "quantity": "10",
        "price": "175.50",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["transaction_type"] == "buy"
    assert float(data["quantity"]) == 10.0
    assert float(data["price"]) == 175.50


@pytest.mark.asyncio
async def test_sell_asset(client, auth_headers):
    portfolios = await client.get("/api/v1/portfolio/", headers=auth_headers)
    portfolio_id = portfolios.json()[0]["id"]

    # Buy first
    await client.post(f"/api/v1/portfolio/{portfolio_id}/buy", headers=auth_headers, json={
        "symbol": "TSLA", "asset_type": "stock", "quantity": "5", "price": "250.00",
    })

    # Sell partial
    resp = await client.post(f"/api/v1/portfolio/{portfolio_id}/sell", headers=auth_headers, json={
        "symbol": "TSLA", "asset_type": "stock", "quantity": "2", "price": "280.00",
    })
    assert resp.status_code == 201
    assert resp.json()["transaction_type"] == "sell"


@pytest.mark.asyncio
async def test_sell_more_than_owned_fails(client, auth_headers):
    portfolios = await client.get("/api/v1/portfolio/", headers=auth_headers)
    portfolio_id = portfolios.json()[0]["id"]

    await client.post(f"/api/v1/portfolio/{portfolio_id}/buy", headers=auth_headers, json={
        "symbol": "MSFT", "asset_type": "stock", "quantity": "3", "price": "400.00",
    })

    resp = await client.post(f"/api/v1/portfolio/{portfolio_id}/sell", headers=auth_headers, json={
        "symbol": "MSFT", "asset_type": "stock", "quantity": "10", "price": "410.00",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_sell_unowned_asset_fails(client, auth_headers):
    portfolios = await client.get("/api/v1/portfolio/", headers=auth_headers)
    portfolio_id = portfolios.json()[0]["id"]

    resp = await client.post(f"/api/v1/portfolio/{portfolio_id}/sell", headers=auth_headers, json={
        "symbol": "NVDA", "asset_type": "stock", "quantity": "1", "price": "800.00",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_transactions(client, auth_headers):
    portfolios = await client.get("/api/v1/portfolio/", headers=auth_headers)
    portfolio_id = portfolios.json()[0]["id"]

    await client.post(f"/api/v1/portfolio/{portfolio_id}/buy", headers=auth_headers, json={
        "symbol": "AMZN", "asset_type": "stock", "quantity": "2", "price": "180.00",
    })

    resp = await client.get(f"/api/v1/portfolio/{portfolio_id}/transactions", headers=auth_headers)
    assert resp.status_code == 200
    txns = resp.json()
    assert len(txns) >= 1
    assert txns[0]["symbol"] == "AMZN"


@pytest.mark.asyncio
async def test_portfolio_isolation_between_users(client):
    """User A should not see User B's portfolio."""
    app.dependency_overrides[get_db] = override_get_db

    for user in [
        {"email": "user_a@test.com", "username": "user_a", "password": "pass12345"},
        {"email": "user_b@test.com", "username": "user_b", "password": "pass12345"},
    ]:
        await client.post("/api/v1/auth/register", json=user)

    login_a = await client.post("/api/v1/auth/login", json={"email": "user_a@test.com", "password": "pass12345"})
    login_b = await client.post("/api/v1/auth/login", json={"email": "user_b@test.com", "password": "pass12345"})
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    portfolios_b = await client.get("/api/v1/portfolio/", headers=headers_b)
    portfolio_b_id = portfolios_b.json()[0]["id"]

    # User A tries to access User B's portfolio
    resp = await client.get(f"/api/v1/portfolio/{portfolio_b_id}", headers=headers_a)
    assert resp.status_code == 403
