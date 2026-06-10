"""
services/risk_service.py — Portfolio and individual asset risk analysis.

Computes: volatility, beta, Sharpe ratio, VaR (95%), max drawdown,
concentration risk, and diversification score.
"""

from datetime import datetime
from typing import Optional
import asyncio
import numpy as np

from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import NotFoundError, ForbiddenError
from core.logging import logger
from database.repositories.portfolio_repository import PortfolioRepository, HoldingRepository
from schemas.schemas import RiskAnalysisResponse, RiskMetrics


RISK_SCORE_THRESHOLDS = {
    "low": 3.0,
    "medium": 6.0,
    "high": 8.0,
}


class RiskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze(
        self,
        user_id: str,
        portfolio_id: Optional[str],
        symbols: Optional[list[str]],
        risk_tolerance: str = "moderate",
    ) -> RiskAnalysisResponse:
        """Main entry point — routes to portfolio or symbol analysis."""
        if portfolio_id:
            return await self._analyze_portfolio(portfolio_id, user_id, risk_tolerance)
        else:
            return await self._analyze_symbols(symbols or [], risk_tolerance)

    async def _analyze_portfolio(
        self, portfolio_id: str, user_id: str, risk_tolerance: str
    ) -> RiskAnalysisResponse:
        repo = PortfolioRepository(self.db)
        portfolio = await repo.get_with_holdings(portfolio_id)
        if not portfolio:
            raise NotFoundError("Portfolio", portfolio_id)
        if portfolio.user_id != user_id:
            raise ForbiddenError()

        symbols = [h.symbol for h in portfolio.holdings]
        if not symbols:
            return self._empty_risk_response()

        # Fetch volatility data for all symbols concurrently
        from tools.financial_tools import calculate_volatility
        tasks = [calculate_volatility(sym) for sym in symbols]
        vol_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate portfolio-level metrics
        vol_data = []
        for r in vol_results:
            if isinstance(r, dict) and "volatility_annual" in r:
                vol_data.append(r)

        if not vol_data:
            return self._empty_risk_response()

        # Weighted portfolio volatility (simplified, equal weight if no values)
        holding_values = []
        for h in portfolio.holdings:
            val = float(h.quantity * (h.current_price or h.average_buy_price))
            holding_values.append(val)

        total_val = sum(holding_values) or 1.0
        weights = [v / total_val for v in holding_values]

        # Concentration risk: Herfindahl index (0 = perfectly diversified, 1 = single asset)
        hhi = sum(w ** 2 for w in weights)
        concentration_risk = round(hhi, 4)
        diversification_score = round(1.0 - hhi, 4)

        vols = [d.get("volatility_annual", 0.2) for d in vol_data]
        avg_vol = float(np.average(vols[:len(weights)], weights=weights[:len(vols)]))

        betas = [d.get("beta") for d in vol_data if d.get("beta") is not None]
        avg_beta = float(np.mean(betas)) if betas else None

        sharpes = [d.get("sharpe_ratio") for d in vol_data if d.get("sharpe_ratio") is not None]
        avg_sharpe = float(np.mean(sharpes)) if sharpes else None

        drawdowns = [d.get("max_drawdown", 0) for d in vol_data]
        worst_drawdown = float(min(drawdowns)) if drawdowns else None

        # VaR 95%: assuming normal distribution, daily VaR scaled to annual
        var_95 = avg_vol * 1.645 / np.sqrt(252) * total_val if avg_vol else None

        metrics = RiskMetrics(
            volatility_30d=round(avg_vol, 4),
            beta=round(avg_beta, 3) if avg_beta else None,
            sharpe_ratio=round(avg_sharpe, 3) if avg_sharpe else None,
            max_drawdown=round(worst_drawdown, 4) if worst_drawdown else None,
            var_95=round(var_95, 2) if var_95 else None,
            concentration_risk=concentration_risk,
            diversification_score=diversification_score,
        )

        risk_score, risk_level, risk_factors, recommendations = self._compute_risk_score(
            metrics, len(symbols), risk_tolerance
        )

        return RiskAnalysisResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            metrics=metrics,
            risk_factors=risk_factors,
            recommendations=recommendations,
            analysis_timestamp=datetime.utcnow(),
        )

    async def _analyze_symbols(
        self, symbols: list[str], risk_tolerance: str
    ) -> RiskAnalysisResponse:
        from tools.financial_tools import calculate_volatility
        tasks = [calculate_volatility(sym) for sym in symbols]
        vol_results = await asyncio.gather(*tasks, return_exceptions=True)

        vol_data = [r for r in vol_results if isinstance(r, dict) and "volatility_annual" in r]
        if not vol_data:
            return self._empty_risk_response()

        vols = [d.get("volatility_annual", 0.2) for d in vol_data]
        avg_vol = float(np.mean(vols))
        betas = [d.get("beta") for d in vol_data if d.get("beta") is not None]
        drawdowns = [d.get("max_drawdown", 0) for d in vol_data]

        metrics = RiskMetrics(
            volatility_30d=round(avg_vol, 4),
            beta=round(float(np.mean(betas)), 3) if betas else None,
            sharpe_ratio=None,
            max_drawdown=round(float(min(drawdowns)), 4) if drawdowns else None,
            var_95=None,
            concentration_risk=round(1.0 / len(symbols), 4) if len(symbols) > 1 else 1.0,
            diversification_score=round(1.0 - 1.0 / len(symbols), 4) if len(symbols) > 1 else 0.0,
        )

        risk_score, risk_level, risk_factors, recommendations = self._compute_risk_score(
            metrics, len(symbols), risk_tolerance
        )

        return RiskAnalysisResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            metrics=metrics,
            risk_factors=risk_factors,
            recommendations=recommendations,
            analysis_timestamp=datetime.utcnow(),
        )

    def _compute_risk_score(
        self, metrics: RiskMetrics, num_assets: int, risk_tolerance: str
    ) -> tuple[float, str, list[str], list[str]]:
        """Score from 0–10 based on multiple risk dimensions."""
        score = 0.0
        risk_factors = []
        recommendations = []

        # Volatility component (0–4 points)
        vol = metrics.volatility_30d or 0.2
        if vol > 0.6:
            score += 4.0
            risk_factors.append(f"Very high annual volatility ({vol:.0%})")
            recommendations.append("Consider reducing position size or hedging")
        elif vol > 0.35:
            score += 2.5
            risk_factors.append(f"High annual volatility ({vol:.0%})")
        elif vol > 0.2:
            score += 1.5
            risk_factors.append(f"Moderate volatility ({vol:.0%})")
        else:
            score += 0.5

        # Beta component (0–2 points)
        beta = metrics.beta
        if beta is not None:
            if beta > 2.0:
                score += 2.0
                risk_factors.append(f"Very high market sensitivity (beta {beta:.2f})")
            elif beta > 1.5:
                score += 1.5
                risk_factors.append(f"High beta ({beta:.2f}) — amplifies market moves")
            elif beta > 1.0:
                score += 1.0
            elif beta < 0:
                score += 0.5
                risk_factors.append(f"Negative beta ({beta:.2f}) — inverse market correlation")

        # Max drawdown component (0–2 points)
        dd = abs(metrics.max_drawdown or 0)
        if dd > 0.5:
            score += 2.0
            risk_factors.append(f"Severe historical drawdown ({dd:.0%})")
            recommendations.append("Review stop-loss levels")
        elif dd > 0.3:
            score += 1.5
            risk_factors.append(f"Significant drawdown history ({dd:.0%})")
        elif dd > 0.15:
            score += 0.5

        # Concentration component (0–2 points)
        conc = metrics.concentration_risk or 0.5
        if num_assets == 1:
            score += 2.0
            risk_factors.append("Single-asset concentration — no diversification")
            recommendations.append("Diversify across at least 5–10 uncorrelated assets")
        elif conc > 0.5:
            score += 1.5
            risk_factors.append(f"High concentration risk (HHI {conc:.2f})")
            recommendations.append("Rebalance to reduce single-asset over-exposure")
        elif conc > 0.25:
            score += 0.5

        # Risk tolerance adjustment
        if risk_tolerance == "conservative" and score > 5:
            risk_factors.append("Portfolio risk exceeds your conservative risk tolerance")
            recommendations.append("Shift toward lower-beta, dividend-paying stocks or bonds")
        elif risk_tolerance == "aggressive" and score < 3:
            recommendations.append("Portfolio is conservatively positioned — consider growth assets")

        score = min(10.0, round(score, 1))

        if score <= RISK_SCORE_THRESHOLDS["low"]:
            risk_level = "low"
        elif score <= RISK_SCORE_THRESHOLDS["medium"]:
            risk_level = "medium"
        elif score <= RISK_SCORE_THRESHOLDS["high"]:
            risk_level = "high"
        else:
            risk_level = "very_high"

        if not recommendations:
            recommendations.append("Portfolio risk profile is within acceptable parameters")

        return score, risk_level, risk_factors, recommendations

    def _empty_risk_response(self) -> RiskAnalysisResponse:
        return RiskAnalysisResponse(
            risk_score=0.0,
            risk_level="low",
            metrics=RiskMetrics(
                volatility_30d=None, beta=None, sharpe_ratio=None,
                max_drawdown=None, var_95=None,
                concentration_risk=None, diversification_score=None,
            ),
            risk_factors=["No holdings to analyze"],
            recommendations=["Add assets to your portfolio to enable risk analysis"],
            analysis_timestamp=datetime.utcnow(),
        )
