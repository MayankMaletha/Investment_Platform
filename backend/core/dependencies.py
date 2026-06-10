"""core/dependencies.py — FastAPI shared dependencies."""

from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import AsyncSessionLocal
from auth.jwt_handler import verify_access_token
from core.exceptions import UnauthorizedError
from services.market_data import FinnhubClient, FinnhubService

security = HTTPBearer()

_finnhub_client: FinnhubClient | None = None
_finnhub_service: FinnhubService | None = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    payload = verify_access_token(token)
    if not payload:
        raise UnauthorizedError("Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token missing subject claim")
    return user_id


async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    from database.repositories.user_repository import UserRepository
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Account is deactivated")
    return user


async def get_finnhub_client() -> FinnhubClient:
    global _finnhub_client
    if _finnhub_client is None:
        _finnhub_client = FinnhubClient()
    return _finnhub_client


async def get_market_data_service(
    client: FinnhubClient = Depends(get_finnhub_client),
) -> FinnhubService:
    global _finnhub_service
    if _finnhub_service is None or _finnhub_service.client is not client:
        _finnhub_service = FinnhubService(client=client)
    return _finnhub_service
