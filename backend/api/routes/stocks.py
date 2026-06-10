"""api/routes/stocks.py — Stock analysis endpoints."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db, get_current_user, get_market_data_service
from database.models.models import User
from schemas.schemas import StockAnalysisRequest, StockAnalysisResponse
from services.analysis_service import AnalysisService
from services.market_data import FinnhubService
from core.logging import logger

router = APIRouter()

@router.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_stock(request: StockAnalysisRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    logger.info("Stock analysis", user_id=current_user.id, symbol=request.symbol)
    service = AnalysisService(db)
    return await service.analyze_stock(request.symbol, current_user.id, current_user.risk_tolerance or "moderate", request)

@router.get("/price/{symbol}")
async def get_price(
    symbol: str,
    current_user: User = Depends(get_current_user),
    market_data: FinnhubService = Depends(get_market_data_service),
):
    result = await market_data.get_quote(symbol)
    return _market_data_response(result)

@router.get("/technical/{symbol}")
async def get_technical(
    symbol: str,
    period: str = Query(default="1y"),
    current_user: User = Depends(get_current_user),
    market_data: FinnhubService = Depends(get_market_data_service),
):
    result = await market_data.get_technical_indicators(symbol, period)
    return _market_data_response(result)


@router.get("/history/{symbol}")
async def get_history(
    symbol: str,
    period: str = Query(default="1y"),
    current_user: User = Depends(get_current_user),
    market_data: FinnhubService = Depends(get_market_data_service),
):
    result = await market_data.get_historical_summary(symbol, period)
    return _market_data_response(result)


@router.get("/volatility/{symbol}")
async def get_volatility(
    symbol: str,
    period: str = Query(default="1y"),
    current_user: User = Depends(get_current_user),
    market_data: FinnhubService = Depends(get_market_data_service),
):
    result = await market_data.get_volatility(symbol, period)
    return _market_data_response(result)


@router.get("/news/{symbol}")
async def get_stock_news(
    symbol: str,
    current_user: User = Depends(get_current_user),
    market_data: FinnhubService = Depends(get_market_data_service),
):
    result = await market_data.get_stock_news(symbol)
    return _market_data_response(result)


def _market_data_response(result: dict):
    if "error" not in result:
        return result
    status_map = {
        "MISSING_API_KEY": 503,
        "RATE_LIMITED": 429,
        "SYMBOL_NOT_FOUND": 404,
        "NO_HISTORICAL_DATA": 404,
        "INSUFFICIENT_DATA": 422,
        "FINNHUB_TIMEOUT": 504,
        "YAHOO_HISTORY_ERROR": 502,
    }
    code = result["error"].get("code", "MARKET_DATA_ERROR")
    return JSONResponse(status_code=status_map.get(code, 502), content=result)
