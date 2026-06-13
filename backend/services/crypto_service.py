"""
services/crypto_service.py - CoinGecko crypto data layer.

Uses CoinGecko for rich crypto market data (no API key needed for basic tier).
"""

from typing import Optional
import aiohttp

from config import settings
from core.logging import logger


# CoinGecko symbol → ID mapping for common coins
COIN_ID_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
    "SOL": "solana", "XRP": "ripple", "ADA": "cardano",
    "DOGE": "dogecoin", "AVAX": "avalanche-2", "DOT": "polkadot",
    "MATIC": "matic-network", "LTC": "litecoin", "LINK": "chainlink",
    "UNI": "uniswap", "ATOM": "cosmos", "XLM": "stellar",
    "USDT": "tether", "USDC": "usd-coin", "SHIB": "shiba-inu",
}


class CryptoService:
    """Fetches and processes cryptocurrency market data."""

    def __init__(self):
        self.base_url = settings.COINGECKO_API_URL
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15),
                headers={"Accept": "application/json"},
            )
        return self._session

    def _symbol_to_id(self, symbol: str) -> str:
        """Convert ticker symbol to CoinGecko ID."""
        return COIN_ID_MAP.get(symbol.upper(), symbol.lower())

    async def get_price(self, symbol: str, vs_currency: str = "usd") -> dict:
        """Get current price and 24h stats for a coin."""
        coin_id = self._symbol_to_id(symbol)
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": vs_currency,
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                    "include_market_cap": "true",
                },
            ) as resp:
                data = await resp.json()
                coin_data = data.get(coin_id, {})
                if not coin_data:
                    return {"symbol": symbol, "error": f"Coin '{symbol}' not found"}

                return {
                    "symbol": symbol.upper(),
                    "coin_id": coin_id,
                    "current_price": coin_data.get(vs_currency),
                    "change_24h": coin_data.get(f"{vs_currency}_24h_change"),
                    "volume_24h": coin_data.get(f"{vs_currency}_24h_vol"),
                    "market_cap": coin_data.get(f"{vs_currency}_market_cap"),
                    "vs_currency": vs_currency,
                }
        except Exception as e:
            logger.error("CoinGecko price fetch failed", symbol=symbol, error=str(e))
            return {
                "symbol": symbol.upper(),
                "error": {
                    "code": "COINGECKO_SERVICE_ERROR",
                    "message": "CoinGecko price fetch failed.",
                },
            }

    async def get_detailed_info(self, symbol: str) -> dict:
        """Get detailed coin information from CoinGecko."""
        coin_id = self._symbol_to_id(symbol)
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/coins/{coin_id}",
                params={"localization": "false", "tickers": "false",
                        "market_data": "true", "community_data": "false"},
            ) as resp:
                if resp.status != 200:
                    return {"symbol": symbol, "error": "Coin not found"}
                data = await resp.json()
                market = data.get("market_data", {})
                return {
                    "symbol": symbol.upper(),
                    "name": data.get("name"),
                    "description": data.get("description", {}).get("en", "")[:500],
                    "current_price_usd": market.get("current_price", {}).get("usd"),
                    "market_cap_usd": market.get("market_cap", {}).get("usd"),
                    "total_volume_usd": market.get("total_volume", {}).get("usd"),
                    "price_change_24h": market.get("price_change_percentage_24h"),
                    "price_change_7d": market.get("price_change_percentage_7d"),
                    "price_change_30d": market.get("price_change_percentage_30d"),
                    "ath": market.get("ath", {}).get("usd"),
                    "ath_change_pct": market.get("ath_change_percentage", {}).get("usd"),
                    "atl": market.get("atl", {}).get("usd"),
                    "circulating_supply": market.get("circulating_supply"),
                    "total_supply": market.get("total_supply"),
                    "market_cap_rank": data.get("market_cap_rank"),
                }
        except Exception as e:
            logger.error("CoinGecko detail fetch failed", symbol=symbol, error=str(e))
            return {"symbol": symbol, "error": str(e)}

    async def get_top_coins(self, limit: int = 20, vs_currency: str = "usd") -> dict:
        """Get top N coins by market cap."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/coins/markets",
                params={
                    "vs_currency": vs_currency,
                    "order": "market_cap_desc",
                    "per_page": limit,
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "24h,7d",
                },
            ) as resp:
                data = await resp.json()
                coins = []
                for c in data:
                    coins.append({
                        "id": c.get("id"),
                        "rank": c.get("market_cap_rank"),
                        "symbol": c.get("symbol", "").upper(),
                        "name": c.get("name"),
                        "image": c.get("image"),
                        "price": c.get("current_price"),
                        "current_price": c.get("current_price"),
                        "price_change_percentage_24h": c.get("price_change_percentage_24h"),
                        "price_change_24h": c.get("price_change_24h"),
                        "market_cap": c.get("market_cap"),
                        "volume_24h": c.get("total_volume"),
                        "change_24h": c.get("price_change_percentage_24h"),
                        "change_7d": c.get("price_change_percentage_7d_in_currency"),
                    })
                return {"coins": coins, "count": len(coins), "vs_currency": vs_currency}
        except Exception as e:
            logger.error("CoinGecko top coins failed", error=str(e))
            return {"coins": [], "error": str(e)}

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
