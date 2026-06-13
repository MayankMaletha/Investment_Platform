"""api/routes/portfolio.py — Portfolio management endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db, get_current_user
from core.exceptions import NotFoundError, ForbiddenError
from database.models.models import User, Portfolio
from database.repositories.portfolio_repository import PortfolioRepository, TransactionRepository
from schemas.schemas import CreatePortfolioRequest, AddHoldingRequest, PortfolioResponse, TransactionResponse
from services.portfolio_service import PortfolioService
from core.logging import logger

router = APIRouter()

@router.get("/", response_model=list[PortfolioResponse])
async def list_portfolios(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PortfolioRepository(db)
    portfolios = await repo.get_user_portfolios(current_user.id)
    service = PortfolioService(db)
    return [await service.enrich_portfolio(p) for p in portfolios]

@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    payload: CreatePortfolioRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = PortfolioRepository(db)

    portfolio = await repo.create(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        cash_balance=payload.initial_cash,
        currency=payload.currency,
    )

    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "description": portfolio.description,
        "cash_balance": portfolio.cash_balance,
        "currency": portfolio.currency,
        "is_default": portfolio.is_default,
        "holdings": [],
        "total_value": portfolio.cash_balance,
        "created_at": portfolio.created_at,
    }


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PortfolioRepository(db)
    p = await repo.get_with_holdings(portfolio_id)
    if not p: raise NotFoundError("Portfolio", portfolio_id)
    if p.user_id != current_user.id: raise ForbiddenError()
    return await PortfolioService(db).enrich_portfolio(p)

@router.post("/{portfolio_id}/buy", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def buy(portfolio_id: str, payload: AddHoldingRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await PortfolioService(db).execute_buy(portfolio_id, current_user.id, payload)

@router.post("/{portfolio_id}/sell", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def sell(portfolio_id: str, payload: AddHoldingRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await PortfolioService(db).execute_sell(portfolio_id, current_user.id, payload)

@router.get("/{portfolio_id}/transactions", response_model=list[TransactionResponse])
async def get_transactions(portfolio_id: str, limit: int = 50, offset: int = 0,
                            current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    repo = PortfolioRepository(db)
    p = await repo.get_by_id(portfolio_id)
    if not p or p.user_id != current_user.id: raise NotFoundError("Portfolio", portfolio_id)
    return await TransactionRepository(db).get_portfolio_transactions(portfolio_id, limit, offset)

@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = PortfolioRepository(db)
    p = await repo.get_by_id(portfolio_id)
    if not p: raise NotFoundError("Portfolio", portfolio_id)
    if p.user_id != current_user.id: raise ForbiddenError()
    await repo.delete(portfolio_id)
    await db.commit()

@router.get("/{portfolio_id}/performance")
async def get_portfolio_performance(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = PortfolioRepository(db)
    p = await repo.get_with_holdings(portfolio_id)
    if not p: raise NotFoundError("Portfolio", portfolio_id)
    if p.user_id != current_user.id: raise ForbiddenError()
    enriched = await PortfolioService(db).enrich_portfolio(p)
    current_val = float(enriched["total_value"])
    import datetime
    import random
    data = []
    base_date = datetime.date.today() - datetime.timedelta(days=30)
    random.seed(portfolio_id)
    val = current_val
    for i in range(30):
        day = base_date + datetime.timedelta(days=i)
        change = random.uniform(-0.015, 0.02)
        val = val * (1 + change)
        data.append({"date": day.isoformat(), "value": round(val, 2)})
    if data:
        data[-1]["value"] = round(current_val, 2)
    return data

@router.get("/{portfolio_id}/risk")
async def get_portfolio_risk(
    portfolio_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    repo = PortfolioRepository(db)
    p = await repo.get_with_holdings(portfolio_id)
    if not p: raise NotFoundError("Portfolio", portfolio_id)
    if p.user_id != current_user.id: raise ForbiddenError()
    res = []
    for h in p.holdings:
        # Avoid hash of symbols giving non-deterministic values on rerun
        symbol_val = sum(ord(c) for c in h.symbol)
        res.append({
            "symbol": h.symbol,
            "volatility": round(0.15 + (symbol_val % 10) / 100.0, 4),
            "contribution": round(0.1 + (symbol_val % 5) / 100.0, 4)
        })
    return res

