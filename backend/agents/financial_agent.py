"""
agents/financial_agent.py — Financial data analysis agent.

Responsibilities:
- Fetch stock/crypto price and fundamental data
- Compute technical indicators
- Summarize financial health metrics
- Output structured financial_data for the graph state
"""

from typing import Any
import asyncio

from core.logging import logger
from tools.financial_tools import (
    get_stock_price_tool,
    calculate_technical_indicators,
    calculate_volatility,
)


class FinancialAgent:
    """Collects and analyzes all financial/market data for a given symbol."""

    async def run(self, symbol: str, asset_type: str = "stock", period: str = "1y") -> dict:
        """
        Execute financial analysis and return structured data.
        Runs price, technical, and volatility fetches concurrently.
        """
        logger.info("FinancialAgent running", symbol=symbol)

        if asset_type == "crypto":
            return await self._analyze_crypto(symbol)
        return await self._analyze_stock(symbol, period)

    async def _analyze_stock(self, symbol: str, period: str) -> dict:
        # Run all three fetches concurrently
        price_task = get_stock_price_tool(symbol)
        tech_task = calculate_technical_indicators(symbol, period)
        vol_task = calculate_volatility(symbol, period)

        price_data, tech_data, vol_data = await asyncio.gather(
            price_task, tech_task, vol_task, return_exceptions=True
        )

        result = {
            "symbol": symbol,
            "asset_type": "stock",
            "price_data": price_data if isinstance(price_data, dict) else {},
            "technical_data": tech_data if isinstance(tech_data, dict) else {},
            "volatility_data": vol_data if isinstance(vol_data, dict) else {},
            "agent": "financial",
        }

        # Extract key signals for the reasoning node
        signals = []
        if isinstance(tech_data, dict) and "signals" in tech_data:
            signals.extend(tech_data["signals"])
        if isinstance(vol_data, dict):
            v = vol_data.get("volatility_annual", 0)
            if v > 0.4: signals.append(f"High volatility ({v:.0%} annual)")
            beta = vol_data.get("beta")
            if beta and beta > 1.5: signals.append(f"High-beta stock ({beta:.2f})")
            if beta and beta < 0.5: signals.append(f"Low-beta defensive stock ({beta:.2f})")

        result["signals"] = signals
        logger.info("FinancialAgent complete", symbol=symbol, signal_count=len(signals))
        return result

    async def _analyze_crypto(self, symbol: str) -> dict:
        from services.crypto_service import CryptoService
        svc = CryptoService()
        price_data = await svc.get_price(symbol)
        detail_data = await svc.get_detailed_info(symbol)
        tech_data = {}

        signals = []
        if isinstance(detail_data, dict):
            chg_30 = detail_data.get("price_change_30d", 0) or 0
            if chg_30 > 20: signals.append(f"Strong 30d uptrend (+{chg_30:.1f}%)")
            elif chg_30 < -20: signals.append(f"Significant 30d decline ({chg_30:.1f}%)")

        return {
            "symbol": symbol,
            "asset_type": "crypto",
            "price_data": price_data,
            "detail_data": detail_data,
            "technical_data": tech_data if isinstance(tech_data, dict) else {},
            "signals": signals,
            "agent": "financial",
        }
