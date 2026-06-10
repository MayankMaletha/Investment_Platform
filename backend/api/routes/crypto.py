"""api/routes/crypto.py — Crypto analysis endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db, get_current_user
from database.models.models import User
from schemas.schemas import CryptoAnalysisRequest, StockAnalysisResponse
from services.analysis_service import AnalysisService

router = APIRouter()

@router.post("/analyze", response_model=StockAnalysisResponse)
async def analyze_crypto(request: CryptoAnalysisRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = AnalysisService(db)
    return await service.analyze_crypto(request.symbol, current_user.id, current_user.risk_tolerance or "moderate", request)

@router.get("/top")
async def get_top_crypto(limit: int = 20, current_user: User = Depends(get_current_user)):
    from services.crypto_service import CryptoService
    return await CryptoService().get_top_coins(limit=limit)

@router.get("/price/{symbol}")
async def get_crypto_price(symbol: str, current_user: User = Depends(get_current_user)):
    from services.crypto_service import CryptoService
    return await CryptoService().get_price(symbol.lower())
