"""api/routes/watchlist.py — Watchlist management."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_user
from core.exceptions import NotFoundError, ForbiddenError, ValidationError
from database.models.models import User, Watchlist
from schemas.schemas import AddWatchlistRequest, WatchlistResponse

router = APIRouter()

@router.get("/", response_model=list[WatchlistResponse])
async def get_watchlist(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Watchlist).where(Watchlist.user_id == current_user.id).order_by(Watchlist.symbol))
    return result.scalars().all()

@router.post("/", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(payload: AddWatchlistRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Watchlist).where(Watchlist.user_id == current_user.id, Watchlist.symbol == payload.symbol))
    if existing.scalar_one_or_none():
        raise ValidationError(f"{payload.symbol} is already in your watchlist")
    item = Watchlist(user_id=current_user.id, symbol=payload.symbol, asset_type=payload.asset_type,
                     notes=payload.notes, alert_price_above=payload.alert_price_above, alert_price_below=payload.alert_price_below)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(item_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Watchlist).where(Watchlist.id == item_id))
    item = result.scalar_one_or_none()
    if not item: raise NotFoundError("Watchlist item", item_id)
    if item.user_id != current_user.id: raise ForbiddenError()
    await db.delete(item)
