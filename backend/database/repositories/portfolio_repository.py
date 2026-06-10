"""database/repositories/portfolio_repository.py — Portfolio data access."""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.models import Portfolio, Holding, Transaction
from database.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    def __init__(self, session: AsyncSession):
        super().__init__(Portfolio, session)

    async def get_user_portfolios(self, user_id: str) -> Sequence[Portfolio]:
        result = await self.session.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
            .options(selectinload(Portfolio.holdings))
            .order_by(Portfolio.is_default.desc(), Portfolio.created_at)
        )
        return result.scalars().all()

    async def get_with_holdings(self, portfolio_id: str) -> Optional[Portfolio]:
        result = await self.session.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
            .options(selectinload(Portfolio.holdings), selectinload(Portfolio.transactions))
        )
        return result.scalar_one_or_none()

    async def get_default(self, user_id: str) -> Optional[Portfolio]:
        result = await self.session.execute(
            select(Portfolio).where(Portfolio.user_id == user_id, Portfolio.is_default == True)
        )
        return result.scalar_one_or_none()


class HoldingRepository(BaseRepository[Holding]):
    def __init__(self, session: AsyncSession):
        super().__init__(Holding, session)

    async def get_by_symbol(self, portfolio_id: str, symbol: str) -> Optional[Holding]:
        result = await self.session.execute(
            select(Holding).where(Holding.portfolio_id == portfolio_id, Holding.symbol == symbol.upper())
        )
        return result.scalar_one_or_none()

    async def get_portfolio_holdings(self, portfolio_id: str) -> Sequence[Holding]:
        result = await self.session.execute(
            select(Holding).where(Holding.portfolio_id == portfolio_id).order_by(Holding.symbol)
        )
        return result.scalars().all()


class TransactionRepository(BaseRepository[Transaction]):
    def __init__(self, session: AsyncSession):
        super().__init__(Transaction, session)

    async def get_portfolio_transactions(self, portfolio_id: str, limit: int = 50, offset: int = 0) -> Sequence[Transaction]:
        result = await self.session.execute(
            select(Transaction).where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.executed_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()
