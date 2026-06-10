"""api/routes/risk.py — Risk analysis endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db, get_current_user
from database.models.models import User
from schemas.schemas import RiskAnalysisRequest, RiskAnalysisResponse
from services.risk_service import RiskService

router = APIRouter()

@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_risk(request: RiskAnalysisRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await RiskService(db).analyze(
        user_id=current_user.id, portfolio_id=request.portfolio_id,
        symbols=request.symbols, risk_tolerance=current_user.risk_tolerance or "moderate",
    )
