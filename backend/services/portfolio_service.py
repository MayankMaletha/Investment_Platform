"""
services/portfolio_service.py — Portfolio business logic.

Handles buy/sell execution, P&L calculation, and portfolio enrichment.
Separating business logic from routes keeps routes thin and this testable.
"""

from decimal import Decimal
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ForbiddenError, InsufficientFundsError, ValidationError
from core.logging import logger
from database.models.models import Portfolio, Holding, Transaction
from database.repositories.portfolio_repository import (
    PortfolioRepository, HoldingRepository, TransactionRepository
)
from schemas.schemas import AddHoldingRequest


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.portfolio_repo = PortfolioRepository(db)
        self.holding_repo = HoldingRepository(db)
        self.tx_repo = TransactionRepository(db)

    async def execute_buy(
        self, portfolio_id: str, user_id: str, payload: AddHoldingRequest
    ) -> Transaction:
        """
        Execute a buy transaction.
        - Validates portfolio ownership
        - Deducts cash if cash tracking is enabled
        - Creates or updates holding with weighted average price
        - Records transaction
        """
        portfolio = await self.portfolio_repo.get_by_id(portfolio_id)
        if not portfolio:
            raise NotFoundError("Portfolio", portfolio_id)
        if portfolio.user_id != user_id:
            raise ForbiddenError()

        total_cost = payload.quantity * payload.price

        # Update or create holding with weighted average cost
        existing = await self.holding_repo.get_by_symbol(portfolio_id, payload.symbol)
        if existing:
            # Weighted average: (old_qty * old_price + new_qty * new_price) / total_qty
            new_qty = existing.quantity + payload.quantity
            new_avg = (
                (existing.quantity * existing.average_buy_price) + (payload.quantity * payload.price)
            ) / new_qty
            await self.holding_repo.update(existing.id, quantity=new_qty, average_buy_price=new_avg)
        else:
            await self.holding_repo.create(
                portfolio_id=portfolio_id,
                symbol=payload.symbol,
                asset_type=payload.asset_type,
                quantity=payload.quantity,
                average_buy_price=payload.price,
            )

        # Record transaction
        tx = await self.tx_repo.create(
            portfolio_id=portfolio_id,
            symbol=payload.symbol,
            asset_type=payload.asset_type,
            transaction_type="buy",
            quantity=payload.quantity,
            price=payload.price,
            total_value=total_cost,
            notes=payload.notes,
        )

        logger.info("Buy executed", portfolio_id=portfolio_id, symbol=payload.symbol, qty=str(payload.quantity))
        return tx

    async def execute_sell(
        self, portfolio_id: str, user_id: str, payload: AddHoldingRequest
    ) -> Transaction:
        """
        Execute a sell transaction.
        - Validates sufficient holdings
        - Reduces or removes the holding
        - Records transaction with realized P&L context
        """
        portfolio = await self.portfolio_repo.get_by_id(portfolio_id)
        if not portfolio:
            raise NotFoundError("Portfolio", portfolio_id)
        if portfolio.user_id != user_id:
            raise ForbiddenError()

        existing = await self.holding_repo.get_by_symbol(portfolio_id, payload.symbol)
        if not existing:
            raise ValidationError(f"No holding found for {payload.symbol}")
        if existing.quantity < payload.quantity:
            raise InsufficientFundsError()

        new_qty = existing.quantity - payload.quantity
        if new_qty == 0:
            await self.holding_repo.delete(existing.id)
        else:
            await self.holding_repo.update(existing.id, quantity=new_qty)

        total_proceeds = payload.quantity * payload.price

        tx = await self.tx_repo.create(
            portfolio_id=portfolio_id,
            symbol=payload.symbol,
            asset_type=payload.asset_type,
            transaction_type="sell",
            quantity=payload.quantity,
            price=payload.price,
            total_value=total_proceeds,
            notes=payload.notes,
        )

        logger.info("Sell executed", portfolio_id=portfolio_id, symbol=payload.symbol)
        return tx

    async def enrich_portfolio(self, portfolio: Portfolio) -> dict:
        """
        Add computed fields to a portfolio: current prices, P&L, total value.
        Fetches live prices for each holding.
        """
        from tools.financial_tools import get_stock_price_tool
        from services.crypto_service import CryptoService

        crypto_svc = CryptoService()
        enriched_holdings = []
        total_market_value = Decimal("0")

        for holding in portfolio.holdings:
            try:
                if holding.asset_type == "crypto":
                    price_data = await crypto_svc.get_price(holding.symbol)
                    current_price = Decimal(str(price_data.get("current_price") or holding.average_buy_price))
                else:
                    price_data = await get_stock_price_tool(holding.symbol)
                    current_price = Decimal(str(price_data.get("current_price") or holding.average_buy_price))

                market_value = holding.quantity * current_price
                cost_basis = holding.quantity * holding.average_buy_price
                unrealized_pnl = market_value - cost_basis
                unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else Decimal("0")

                total_market_value += market_value

                enriched_holdings.append({
                    "id": holding.id,
                    "symbol": holding.symbol,
                    "asset_type": holding.asset_type,
                    "quantity": holding.quantity,
                    "average_buy_price": holding.average_buy_price,
                    "current_price": current_price,
                    "market_value": round(market_value, 2),
                    "unrealized_pnl": round(unrealized_pnl, 2),
                    "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                })
            except Exception as e:
                logger.warning("Price fetch failed for holding", symbol=holding.symbol, error=str(e))
                enriched_holdings.append({
                    "id": holding.id,
                    "symbol": holding.symbol,
                    "asset_type": holding.asset_type,
                    "quantity": holding.quantity,
                    "average_buy_price": holding.average_buy_price,
                    "current_price": None,
                    "market_value": None,
                    "unrealized_pnl": None,
                    "unrealized_pnl_pct": None,
                })

        total_value = total_market_value + portfolio.cash_balance

        return {
            "id": portfolio.id,
            "name": portfolio.name,
            "description": portfolio.description,
            "cash_balance": portfolio.cash_balance,
            "currency": portfolio.currency,
            "is_default": portfolio.is_default,
            "holdings": enriched_holdings,
            "total_market_value": round(total_market_value, 2),
            "total_value": round(total_value, 2),
            "created_at": portfolio.created_at,
        }
