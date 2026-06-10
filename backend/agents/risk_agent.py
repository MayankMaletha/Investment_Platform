"""
agents/risk_agent.py — Real-time risk assessment agent for the workflow.

Calculates risk profile for the target symbol and (optionally) its
impact on an existing portfolio.
"""

from core.logging import logger
from tools.financial_tools import calculate_volatility


class RiskAgent:
    """Assesses risk for a symbol in the context of the multi-agent workflow."""

    async def run(
        self, symbol: str, portfolio_context: dict | None = None
    ) -> dict:
        logger.info("RiskAgent running", symbol=symbol)

        vol_data = await calculate_volatility(symbol)
        if "error" in vol_data:
            return {"symbol": symbol, "risk_level": "unknown", "agent": "risk", "error": vol_data["error"]}

        vol = vol_data.get("volatility_annual", 0.2)
        beta = vol_data.get("beta")
        max_dd = abs(vol_data.get("max_drawdown", 0))
        sharpe = vol_data.get("sharpe_ratio")

        # Build risk profile
        risk_factors = []
        risk_score = 0.0

        if vol > 0.5:
            risk_score += 3.0
            risk_factors.append(f"Very high volatility ({vol:.0%})")
        elif vol > 0.3:
            risk_score += 2.0
            risk_factors.append(f"High volatility ({vol:.0%})")
        elif vol > 0.15:
            risk_score += 1.0

        if beta and beta > 1.5:
            risk_score += 2.0
            risk_factors.append(f"High market sensitivity (β={beta:.2f})")
        elif beta and beta < 0:
            risk_score += 1.5
            risk_factors.append(f"Inverse market correlation (β={beta:.2f})")

        if max_dd > 0.4:
            risk_score += 2.0
            risk_factors.append(f"Large historical drawdown ({max_dd:.0%})")
        elif max_dd > 0.25:
            risk_score += 1.0
            risk_factors.append(f"Notable drawdown history ({max_dd:.0%})")

        risk_score = min(10.0, round(risk_score, 1))
        if risk_score < 3: risk_level = "low"
        elif risk_score < 6: risk_level = "medium"
        elif risk_score < 8: risk_level = "high"
        else: risk_level = "very_high"

        # Portfolio impact assessment
        portfolio_impact = None
        if portfolio_context and portfolio_context.get("holdings"):
            holdings = portfolio_context["holdings"]
            total_val = sum(float(h.get("market_value") or 0) for h in holdings)
            if total_val > 0:
                portfolio_impact = {
                    "would_increase_concentration": len(holdings) < 5,
                    "suggestion": "This would reduce diversification" if len(holdings) < 5
                                  else "Portfolio has adequate diversification",
                }

        result = {
            "symbol": symbol,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "volatility_annual": round(vol, 4),
            "beta": beta,
            "max_drawdown": round(max_dd, 4),
            "sharpe_ratio": sharpe,
            "portfolio_impact": portfolio_impact,
            "agent": "risk",
        }
        logger.info("RiskAgent complete", symbol=symbol, risk_level=risk_level)
        return result
