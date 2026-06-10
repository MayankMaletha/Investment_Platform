"""api/routes/news.py — Market news endpoints."""

from fastapi import APIRouter, Depends, Query
from core.dependencies import get_current_user
from database.models.models import User
from schemas.schemas import NewsResponse
from services.news_service import NewsService

router = APIRouter()

@router.get("/market", response_model=NewsResponse)
async def get_market_news(
    query: str = Query(default="stock market", min_length=2),
    page_size: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    return await NewsService().get_analyzed_news(query=query, page_size=page_size)

@router.get("/symbol/{symbol}", response_model=NewsResponse)
async def get_symbol_news(
    symbol: str,
    page_size: int = Query(default=10, ge=1, le=30),
    current_user: User = Depends(get_current_user),
):
    return await NewsService().get_analyzed_news(query=symbol.upper(), page_size=page_size)
